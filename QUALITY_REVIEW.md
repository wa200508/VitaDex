# VitaDex quality and intent review

Baseline review on 2026-11-02 against the then-current local working tree.
The findings below are historical: the first-five implementation follow-up is in
[docs/review/TOP_FIVE.md](docs/review/TOP_FIVE.md), with current acceptance status
in [BACKLOG.md](BACKLOG.md). This is not a review of a pushed release. No application behavior was changed
as part of this review. [BACKLOG.md](BACKLOG.md) is the actionable next-work list;
[ROADMAP.md](ROADMAP.md) summarizes the delivery sequence.

## Assessment

The prototype follows the intended product direction: a mobile nature companion
that introduces a first discovery aloud, preserves a card, and supports returning
to learn from cited information. It has a useful computer preview and a five-entry
Ohio starter catalog. It is not yet a mobile-ready application or a complete
source-grounded learning experience. Resolve integrity and lifecycle gaps before
expanding features, then finish one discovery-to-question experience.

The governing requirements are [PRODUCT.md](PRODUCT.md),
[BATTERY_POLICY.md](BATTERY_POLICY.md), [SOURCE_POLICY.md](SOURCE_POLICY.md), and
[ART_DIRECTION.md](ART_DIRECTION.md). Final illustrations are explicitly deferred.

## Verification performed

- Ruff: passed the repository's configured F checks (undefined names, imports,
  etc.). This is a narrow lint configuration, not a broad maintainability review.
- Pytest: **57 passed**. One warning comes from the installed external AnyIO
  pytest plugin's use of a deprecated pytest API, not an app test failure.
- Compile: all application modules and scripts passed `compileall`.
- `git diff --check`: passed.
- Real Kivy UI script: passed discovery, saved cards, search, type filtering,
  sorting, seen-state persistence, failed saves, repeat suppression, replay,
  detail popup, and a 360×640 layout check. It uses a silent injected speaker;
  it does not verify audible playback, touch ergonomics, or accessibility.
- Five targeted probes reproduced the failures below. Results are in
  [docs/review/2026-11-02-probes.txt](docs/review/2026-11-02-probes.txt).
  The archived probe script records the pre-fix behavior; it is not expected to
  run unchanged against the corrected implementation. Current regression tests
  are in `tests/test_integrity_regressions.py`.
  Probe data is isolated in a temporary directory; production journals/catalogs
  are not modified. The probes demonstrate gaps; they are not passing acceptance
  tests for fixes.

Not performed: installation on Android/iOS, audible speech validation, battery or
thermal profiling, six-year-old usability sessions, independent editorial review,
source link rechecking, or provider-backed chat evaluation. This review checked
source metadata and its treatment in code; it did not re-fact-check the catalog.

## Alignment with product intent

| Intent | Present behavior | Remaining gap |
| --- | --- | --- |
| Mobile app only | Kivy UI with computer preview and mobile speech hooks | No mobile packaging/build pipeline or device evidence |
| First discovery says the name and introduces the organism | Saved introduction requested after successful persistence; written card and replay | Speech completion/cancellation not represented; duplicate identity and concurrent-arrival gaps |
| Repeated familiar organisms stay quiet | Same-key repeats suppressed across restarts; badge state is separate | Scientific-name aliases and eventual multiple sensor inputs can bypass this |
| Cards support later learning | Five Ohio entries; search, filters, sorting, sources, and replay | No notes, favorites, encounter history, backup/export, or chat |
| Information pedigree | Field-linked references, access dates, excerpts, attribution, source-check status | Human review pending; display-field consistency and source update workflow incomplete |
| Minimal power use | No sensing/background capture; local cards/art; speech worker waits on a queue | Collection-wide rewrites/rebuilds; no phone measurements; mobile speech may outlive pause |
| Realistic anime art highlights described traits | Target documented; generated study kept outside runtime | Vector placeholders remain as authorized; no production asset/framing/review pipeline |
| Six-year-old everyday Ohio experience | Dog, cat, red maple, Kentucky bluegrass, robin; short introductions | Sources and technical metadata mixed into long detail views; no child testing |
| Ask questions using trusted sources and a selected LLM | Provider-neutral design documented | Source ingestion, retrieval, provider setup, citations, and chat UI absent |

## Findings, ordered by next-work priority

### F01 — interrupted migration can strand an older collection (high)

`journal.py:28` migrates only if the destination path does not exist. A valid legacy
JSON with one card plus an empty SQLite file loads **zero** cards. An interrupted
initial migration can leave that state. The original JSON remains intact, but
subsequent startup skips it and presents an empty journal. Do not equate file
existence with completed migration. Track migration completion transactionally and
make retry/recovery explicit. Backlog **VD-01**.

### F02 — speech lifecycle does not yet meet the mobile interaction (high)

`narration.py:36` cannot stop the mobile facade's in-progress playback, despite
`main.py:594` calling it on pause. The worker has no shutdown sentinel, no playback
completion events, and no explicit session/utterance identity. A late error uses
`main.py:565`'s most recently assigned card label and may report against another
open card. `speak()` replaces a waiting introduction silently. These are code
observations, not phone-reproduced failures. Fix and device-test before claiming
quiet-on-background behavior or reliable first-introduction playback. **VD-02**.

### F03 — names are not a reliable discovery identity (high)

`discovery.py:13` builds keys from scientific-name text. A dog under the two
scientific names already discussed in the card, `Canis lupus familiaris` and
`Canis familiaris`, produces **two first discoveries and two cards**. Legacy
fallback uses common-name matching. Catalog progress also uses display names.
Use stable organism IDs and explicit aliases with a snapshot migration. **VD-03**.

### F04 — first discovery is not atomic across arrivals (high before sensing)

`discovery.py:42` checks the in-memory collection and saves in separate steps.
Two coordinated calls to the same service both return `is_first=True`, adding
two in-memory cards. The current manual UI is sequential; the risk becomes real
when camera/audio/worker callbacks converge. Enforce uniqueness in storage, make
creation atomic, and marshal UI work to its thread. **VD-03**.

### F05 — local catalog validation accepts malformed factual fields (high)

`database.py:90` and `provenance.py` validate section structure and citation
coverage but do not apply the full schema/type contract at normal catalog load.
Setting a source-checked entry's description to integer `17` still constructs a
catalog. Later narration/UI assumes strings. Sync's schema validation does not
protect local bundles or other direct callers. Use one validation boundary for
loading, syncing, and snapshot recovery. **VD-04**.

### F06 — displayed claim values can diverge from cited facts (high)

`journal.py:125` checks that `selected_details` are strings, but not that Habitat
and Size match their organism snapshot. A substituted habitat survives save/load,
and `main.py` still attaches the original habitat citation IDs to it. This is a
consistency defect, not evidence that current starter facts are wrong. Remove
redundant derived values or enforce source-to-displayed-value consistency;
preserve historical source versions rather than silently replacing them. **VD-04**.

### F07 — current collection operations scale against the energy requirement (medium)

`journal.py:49` serializes, validates, deletes, and reinserts the entire collection
for every addition. `main.py:531` refreshes both home and card-book views;
`CardBookScreen.refresh_cards()` rebuilds all tiles even when hidden, including
on search keystrokes. Voice status updates also rebuild recent-card widgets.
There is no busy discovery polling, but these avoidable operations are not a
battery-efficient basis for a growing collection. Introduce incremental records,
updates, and virtualized visible items, then measure. **VD-05**.

### F08 — mobile, energy, and accessibility claims remain unproven (release gap)

There is no Buildozer/iOS build configuration or mobile CI. The preview cannot
verify speech routing, lock/pause behavior, native resource disposal, screen-reader
support, safe areas, text scaling, or energy. Do a minimal device build early,
without pulling camera implementation ahead of core feature work. **VD-07/08/09**.

### F09 — trusted learning and chat are incomplete (feature/editorial gap)

The starter catalog transparently labels AI source checking and pending human
review, which is appropriate. Brief verification excerpts are not an adequate
retrieval corpus for general organism questions. Metadata validation does not
establish authoritative publishers, factual support, approval authenticity, or
bulk-text reuse rights. Finish editorial workflow and permitted source passages
before adding provider-generated answers. **VD-06/10/11**.

### F10 — quality tooling does not cover the highest-risk paths (medium)

Current CI runs Python tests/lint/explicit compilation on Python 3.11/3.12.
It does not run the UI script, mobile builds, or energy/lifecycle checks; Python
3.13 is allowed in project metadata but not in the matrix. Speech tests cover an
engine error, not queue replacement, cancellation, callbacks, or completion.
Add regressions for F01–F06 as their fixes land. **VD-12**.

### F11 — catalog sync can damage the local content bundle on failure (medium)

`scripts/sync_card_db.py` uses `urlopen` without a timeout and overwrites the target
with `open('w')`, without atomic replacement or a backup. Its import of `database`
also loads the existing global catalog, so a corrupt current catalog can prevent
repair with a valid download. Isolate validation from global loading and make the
update bounded, validated, atomic, and recoverable. **VD-13**.

## Positive foundations worth retaining

Save-before-announcement, transactional card replacement, read-error write
protection, original card/source snapshots, explicit uncertainty handling,
persistent seen/voice settings, clear simulation labeling, and local placeholder
art are useful foundations. The blocked speech queue does not busy-spin. No live
LLM calls, capture loops, or background sensing have been introduced.

## Recommended decision

Treat the current tree as a feature prototype. Next implement **VD-01 through
VD-04**, with regressions. Then reduce avoidable collection work and finish a
small discovery-to-cited-question experience. Start a minimal phone-build spike
in that next milestone so native speech and energy risks are discovered early.
Keep final art, passive sensing, and catalog expansion out of the critical path.
