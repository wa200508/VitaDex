# VitaDex backlog

Created 2026-11-02 from [QUALITY_REVIEW.md](QUALITY_REVIEW.md). Status updates are recorded below. Items without a status note are **open**. Requirements and acceptance criteria are recorded here; they do not
claim implementation. IDs are stable so future commits/issues can reference them.

Priority: **P0** = next integrity/core-behavior work; **P1** = first useful mobile
learning experience; **P2** = subsequent enrichment. P0 does not mean the prototype
has already shipped a critical incident. Sizes are relative: S = bounded change,
M = multiple modules/tests, L = significant feature or device integration.

## Next: fix integrity and first-discovery behavior

### VD-01 · P0 · M · Recover interrupted journal migration

**Status: implemented and regression-tested locally.** Transactional completion marker, resumable empty-file migration, preserved backups, and no resurrection after an intentional empty save. Mobile release testing remains separate.

Evidence: F01, `journal.py:28`.

Acceptance: migration completion is recorded with the migrated cards in one
transaction. An interrupted attempt with an empty/partially initialized SQLite
file can resume or offers explicit safe recovery; a populated journal is never
silently merged/replaced. Retain legacy backups. Test interruption before and
after commit, malformed legacy input, and repeat startup. No introduction or
collection replacement follows a storage failure. Depends: none.

### VD-02 · P0 · L · Give speech a complete lifecycle

**Status: implementation and deterministic tests complete; actual-device acceptance pending VD-07/08.** Per-utterance/card events, bounded FIFO with explicit overflow, cancellation, pause/resume, shutdown, UI callback isolation, and native ownership adapters are present. Android/iOS playback and interruption are not claimed verified.

Evidence: F02, `narration.py`, `main.py:557`.

Acceptance: native adapters report requested/started/completed/cancelled/failed
against an utterance/card ID. Replay, mute, pause, lock, stop, and shutdown have
explicit behavior. No stale callback updates a different card; no silently lost
first introduction or overlapping mobile playback. Queues stay bounded and workers
can shut down. Written content survives any audio error. Add deterministic queue,
cancellation, and callback tests; phone checks in VD-08 gate mobile completion.
Depends: none; VD-07/08 for actual-device acceptance.

### VD-03 · P0 · L · Make first discovery atomic and species identity stable

**Status: implemented and regression-tested locally.** Bundled IDs/aliases, additive discovery index for historical snapshots, transactional database uniqueness, session locking/indexes, and UI-thread dispatch. Existing duplicate snapshots are retained rather than silently deleted.

Evidence: F03/F04, `discovery.py`.

Acceptance: durable organism IDs and explicit taxonomic aliases map the two dog
names to one species. Storage enforces discovery uniqueness; concurrent arrivals
produce one saved card and one first-discovery event. Migrate older snapshots
without discarding cards or resetting first-discovery history. Identity-based
progress survives renames. Seen badges remain separate. Test aliases, concurrency,
restart, legacy names, and uncertain/no-match input. Depends: VD-01 migration design.

### VD-04 · P0 · M · Unify catalog, snapshot, and displayed-fact validation

**Status: implemented and regression-tested locally.** Shared field/type validation at catalog loading/sync/build and journal restoration; displayed derived facts must match their saved source-bearing organism. Invalid snapshots remain protected rather than being silently rewritten.

Evidence: F05/F06, `database.py`, `provenance.py`, `journal.py`.

Acceptance: direct load, sync, and journal restore enforce consistent field types
and citation/evidence constraints. A numeric description is rejected with an
actionable error before UI use. Displayed Habitat/Size cannot inherit citations
for different values. Preserve versioned historical facts and sources; quarantine
invalid records or report recoverable errors without erasing the journal. Tests
cover malformed nested values, claim drift, and old valid snapshots. Depends: none.

## Then: complete a small learning experience, with early phone validation

### VD-05 · P1 · L · Make collection work incremental and measurable

**Status: implemented and measured on desktop; device energy acceptance pending VD-09.** Incremental writes, indexed discovery identity, cached new-card membership, unchanged/hidden-view reuse, debounced search, and bounded 12-card pages replace full collection rendering. Pagination is the bounded-rendering approach for this preview; initial catalog/journal loading still scales with collection size. See `docs/review/collection-after.json` and `scripts/measure_collection.py`.

Evidence: F07, `JournalRepository.save_cards`, view refresh methods.

Acceptance: one discovery writes only necessary records atomically; normal
browsing/status changes do not rewrite collection data. Hidden collections do
not rebuild on unrelated events. Reuse visible tiles/textures, virtualize or paginate large
lists, and avoid unbounded search work per keystroke. Instrument small and large
collections and record latency, writes, widget creation, and device energy when
available. Do not invent a battery target from desktop timing. Depends: VD-03/04.

### VD-06 · P1 · M · Finish the Ohio starter editorial workflow

**Status: workflow implemented; actual independent human sign-off remains pending.** Version-bound packets, completeness/staleness checks, separate proposed catalog output, explicit update previews, archived prior snapshots, and regression coverage. No entries have been falsely promoted to human-reviewed.

Evidence: F09; `OHIO_STARTER.md` and `SOURCE_POLICY.md`.

Acceptance: independent human review is recorded honestly per entry and source
version. Keep source-checked status until that happens. Review scientific names,
child-readable introductions, field-to-source support, and reference/quotation
reuse terms. Separate corrected source versions from existing card snapshots;
offer a transparent update path. Test citation completeness and evidence integrity.
Depends: VD-04; human editorial work is an external dependency, not assumed approval.

### VD-07 · P1 · M · Produce one installable mobile preview early

**Status: Android build spike configured and running through CI; installation/device acceptance pending.** Pinned build inputs, offline bundled data, TTS queries, APK content/permission checks, and artifact job. Android is provisional pending phone preference. Local build lacks javac; initial remote dependency conflict was corrected. See `MOBILE_PREVIEW.md` and current build evidence in `docs/review/NEXT_FIVE.md`.

Evidence: F08; currently no mobile build configuration.

Acceptance: document the initial Android/iOS target, pin a working build toolchain,
bundle catalog/source data correctly, and provide reproducible build/install steps.
The preview works offline for simulated discovery, journal browsing, and supported
system-voice replay. It requests no camera/microphone permissions yet. Maintain
computer preview solely as a development aid. Depends: initial phone/platform
selection; VD-08 validates the resulting build.

### VD-08 · P1 · M · Validate native speech and app lifecycle on a phone

**Status: test tooling prepared; actual phone validation remains open.** Offline Android voice selection, opt-in bounded local event tracing, an unfilled acceptance template, and repeatable audio/lifecycle steps are present. No device result is marked passed.

Evidence: F02/F08, `BATTERY_POLICY.md`.

Acceptance: record device/OS and results for first introduction, duplicate silence,
replay, disabled auto voice, audio routing, interruption, pause/resume, lock,
shutdown, missing voice, and offline startup. Fix native resource disposal and
cancellation. Add a repeatable checklist/automated coverage where feasible.
Depends: VD-02/07.

### VD-09 · P1 · M · Establish an energy baseline and regression budgets

**Status: read-only capture tooling and unfilled baseline/budget templates prepared; real measurements and numerical budgets remain open.** No energy estimate is inferred from desktop tests or raw battery percentage.

Evidence: F07/F08; no battery measurements exist.

Acceptance: use real-device profilers for idle, browsing a large collection,
discovery, repeated discovery, narration, and background/lock. Verify no recurring
recognition/network work or app-requested wake locks. Record brightness, network,
thermal state, caches, and workload. Set numerical budgets from the evidence;
repeat after major changes. Later add chat/capture workloads, without claiming
that duplicate suppression alone saves sensing energy. Depends: VD-05/07/08.

### VD-10 · P1 · L · Prepare a small permitted source-passage corpus

**Status: a validated, offline editorial-summary corpus and scoped retrieval are implemented; larger licensed primary-source ingestion and human approval remain open.** Passage/source hashes, attribution, explicit reuse basis, evaluation questions, unsupported-query behavior, saved-snapshot context, and reviewed-only default retrieval are tested. Source-checked preview requires explicit opt-in; no live model/chat UI.

Evidence: F09; brief verification excerpts are not a general Q&A corpus.

Acceptance: for the five starter organisms, store usable passages with source ID,
location, version/access date, content hash, attribution, and explicit reuse
basis. Distinguish source text, editorial paraphrases, personal notes, and game
content. Retrieve only relevant organism evidence. Define supported and deliberately
unsupported questions; never fetch entire sites automatically on card open.
Depends: VD-04/06; rights review for any text beyond current short excerpts.

### VD-11 · P1 · L · Add the first cited “Ask VitaDex” flow

Acceptance: a selected card offers a question UI and a user-selected provider/model
adapter. Retrieve before generating; show supporting passage citations and source
links, and abstain when evidence is insufficient or conflicting. Test incorrect
citation IDs, prompt injection in source text, unsupported biological claims,
provider failure/offline behavior, cancellation, and bounded context/output.
Keep keys in platform-appropriate secure storage and explain what leaves the
device. No automatic chat requests on discovery. Spoken answers are deliberate.
Depends: VD-10 and provider configuration; no invented provider credentials.

### VD-12 · P1 · M · Extend quality gates around the actual risks

Evidence: F10; current suite passes but misses review probes.

Acceptance: turn VD-01–04 probes into regressions when fixes land. Add deterministic
speech lifecycle tests and a runnable headless UI job where supported. Align the
supported Python matrix with metadata (currently 3.13 is not in CI), document
mobile/manual gates, and establish dependency/build reproducibility. Keep energy
and actual audio claims separate from mocked tests. Depends: alongside fixes,
not an excuse to delay them.

### VD-13 · P1 · M · Make catalog sync bounded, atomic, and repairable

Evidence: F11; `scripts/sync_card_db.py`.

Acceptance: finite network timeouts and clear failures; validated temporary output
replaces the catalog atomically, retaining an appropriate prior version. A corrupt
existing catalog must not prevent validation/restoration of a replacement. Loading
validation code must not eagerly require a healthy global catalog. Test interrupted
write, invalid download, offline timeout, and corrupt-current/valid-new recovery.
Depends: VD-04.

### VD-14 · P1 · M · Polish discovery and detail views for young learners

Evidence: current screen/detail design; six-year-old usability untested.

Acceptance: name, introduction, and listen/stop controls are immediately useful at
phone size. Put advanced source/reviewer details in an easy-to-find secondary
section while keeping citation access visible. Clearly distinguish simulated
selection, uncertain candidates, and confirmed observations. Handle safe areas,
large text, screen readers, touch targets, back navigation, and error states.
Test reading/listening with a child and adult. No final art requirement.
Depends: VD-02; device checks with VD-07.

## Later: enrich the journal without compromising power or trust

### VD-15 · P2 · M · Add journal backup/export and safe restore

Acceptance: export/import cards, provenance, discovery IDs, and relevant settings;
validate versions and references before import, resolve duplicates, preview changes,
and preserve backups. A failed import never overwrites valid data. Depends: VD-01/03/04.

### VD-16 · P2 · M · Add notes, favorites, and deliberate collection management

Acceptance: notes have edit/save/cancel; favorites have a filter; deletion has clear
confirmation. Decide whether removing a visible card should forget a species
before implementing it; do not accidentally cause familiar pets to announce again.
Personal notes cannot become trusted RAG evidence. Seen state must not rely on a
fragile position count after deletions. Depends: VD-03/05/15.

### VD-17 · P2 · L · Add bounded, deliberate capture and encounter history

Acceptance: explicit start/end/time limit, sensor release on completion/error/
pause/lock, denied-permission and uncertainty UI, and observation time/input/source
separate from species facts. No default passive microphone/camera sensing. Confirm
matches before a real discovery; route them through atomic VD-03 behavior. Measure
energy before expanding frequency or duration. Depends: VD-03/07/08/09/14 and a
separately selected, evaluated identification model.

### VD-18 · P2 · L · Replace placeholders with approved trait-focused art

Acceptance: artwork follows `ART_DIRECTION.md`: realistic anime finish, natural
anatomy, and viewpoints emphasizing the cited description. Check traits and phone
framing, record origin/rights/review, and bundle efficient static assets with
texture reuse. Generated study remains unapproved until reviewed. No on-device
art generation or background downloads. Depends: stable content/briefs in VD-06;
explicitly not a blocker for earlier feature milestones.

### VD-19 · P2 · M · Expand regional content with the same evidence standard

Acceptance: add familiar Ohio organisms only with stable IDs, cited short
introductions, honest review status, useful source passages, and later approved
illustrations. Measure pronunciation/reading clarity and avoid ambiguous grass/
maple labels. Do not prioritize catalog size over a complete learning loop.
Depends: VD-03/06/10.

### VD-20 · P2 · S · Clarify publication, content, and development documentation

Acceptance: keep one authoritative backlog; show shipped/preview/planned status
consistently. Reconcile README's restrictive license wording with the repository's
GPL license file and source/asset-specific notices before distribution; document
intended terms without silently changing them. Describe optional ComfyUI utilities
as outside the core mobile path. Publish a reviewable branch/PR when moving local
work to GitHub; do not describe unpushed changes as available on main.
Depends: owner decisions on intended publication terms.

## Suggested delivery order

1. **Integrity pass:** VD-01, VD-04, VD-03, VD-02; add regressions through VD-12.
2. **Useful five-card experience:** VD-05/06/13/14, source passages VD-10, then
   provider-backed questions VD-11. Start VD-07 early here; do not wait for chat
   or final artwork to find native-platform problems.
3. **Mobile readiness:** VD-08/09 and remaining accessibility checks. A feature
   preview can precede this; claims of reliable mobile narration/energy cannot.
4. **Enrichment:** backup and journal tools, then bounded sensing, reviewed art,
   and more organisms as evidence and capacity permit.

Do not build a web version, passive sensing, new image-generation features, or
more decorative UI ahead of the core work above. Placeholder art is acceptable.
