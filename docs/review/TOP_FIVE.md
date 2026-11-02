# First-five backlog implementation follow-up

Updated 2026-11-02. All changes are local and unpushed. This report supersedes the
baseline review's recommendation to begin VD-01–05. It does not supersede the
baseline's warnings about device validation and source/editorial gaps.

## Delivered

| Item | Implementation | Acceptance status |
| --- | --- | --- |
| VD-01 migration | Completion marker committed with import; interrupted empty SQLite retries; populated/explicitly emptied journals do not re-import legacy backup | Regression-tested locally |
| VD-02 speech | Requested/started/completed/cancelled/failed events identify utterance/card; bounded FIFO reports overflow; stop, pause/resume, shutdown sentinel; native Android/iOS ownership/cancellation; stale UI errors isolated | Deterministic and UI tests pass; phone acceptance remains open |
| VD-03 discovery identity | Explicit stable IDs, dog taxonomic aliases, durable unique discovery index, transactionally claimed first discovery, session locking/indexing, main-thread UI dispatch | Alias/restart and two-session concurrent-arrival tests pass |
| VD-04 facts | Shared dataclass field contract for catalog/sync/snapshots; nested provenance checks; displayed derived facts must match source-bearing snapshot | Malformed types, inconsistent claims, and preservation regressions pass |
| VD-05 collection cost | Single-record append; no normal full journal replacement; indexed lookup; new-card cache; no hidden/unchanged tile rebuild; search debounce; bounded 12-card pages | SQL write and UI reuse/page tests pass; desktop baseline recorded; phone energy gate open |

Migration is additive within the existing SQLite format. It preserves original
card/source snapshots, maps existing records into a separate discovery index, and
keeps historical duplicates rather than silently deleting observations. Current
first-discovery uniqueness is enforced in storage, even between separate sessions.
Bulk replacement remains available for explicit snapshot operations and tests;
normal additions do not use it.

The validation module enforces shared field types and required fields. Catalog
invariants, source metadata/evidence checks, and snapshot consistency add their
contextual checks. This is not a replacement for source accuracy/editorial review.

Bounded paging avoids creating every card widget at once. Search/filtering and
initial loading still examine stored in-memory data, and full database startup
validation still scales with the journal. A larger persistent index/lazy loading
can follow measurements; no universal performance or energy guarantee is made.

## Evidence

- `python -m pytest`: **70 passed**, including migration interruption/rollback,
  scientific aliases/renames, concurrent sessions, malformed facts, source-field
  drift, single-record writes, speech queue overflow/events/cancellation/shutdown,
  and a simulated native lifecycle handle.
- Ruff and compilation pass. The known external AnyIO/pytest deprecation warning
  remains outside the application implementation.
- `scripts/check_ui.py` passes discovery/replay, persistence, errors, filters,
  paging, unchanged and hidden-view reuse, late speech error isolation,
  pause/resume dispatch, and narrow-layout checks. It uses a silent test speaker.
- `scripts/measure_collection.py` records desktop append cost and card writes for
  10 and 1,000 existing cards in `collection-after.json`. Each append writes one
  card. Timing is a single local sample, not a benchmark guarantee or energy result.

No new camera, microphone, remote-model requests, or background downloads were
introduced. Background encounters are ignored while the application is paused.

## Remaining acceptance gates

Native Android/iOS initialization, audible output, cancellation, interruption,
lock behavior, resource disposal, and pronunciation require an installable build
and real-device checks (VD-07/08). The adapters perform bounded status polling only
while native speech is active; this behavior and completion timing must be checked
on devices. Mocked native handles do not prove framework integration.

Battery/thermal claims require VD-09. Large-text/screen-reader behavior and child
usability remain in VD-14. Independent source review remains VD-06. These are
open work, not prerequisites we can silently declare satisfied from desktop tests.
