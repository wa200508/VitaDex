# Application structure

`main.py` is the mobile/desktop entry point. `application.py` owns app lifecycle,
service wiring, discovery dispatch, narration events, and navigation. Views do
not own journal transactions or model request execution.

| Module | Responsibility |
| --- | --- |
| `vitadex_ui/widgets.py`, `art.py` | Shared visual primitives, palette, procedural placeholder art |
| `vitadex_ui/screens.py` | Journal, simulated discovery, bounded card-book pages |
| `vitadex_ui/dialogs.py` | Card details, citations, explicit fact update previews |
| `vitadex_ui/questions.py` | Question form, evidence display, session-only key field |
| `questions.py` | One cancellable worker; generation-bound delivery; key cleanup; no Kivy dependency |
| `ask.py`, `corpus.py` | Retrieved evidence, optional provider passage selection, citation-bound answers |
| `journal.py`, `identity.py`, `discovery.py` | SQLite snapshots, stable species identity, atomic first discoveries |
| `backup.py` | Validated portable snapshots, preview, merge/replace, safety copy, transactional restore |
| `documents.py`, `vitadex_ui/documents.py` | Bounded atomic local copies, desktop picker, Android document intents |
| `vitadex_ui/backups.py` | Explicit export/restore controls; blocking file/validation work on demand in a worker |
| `narration.py`, `native_speech.py` | Bounded speech lifecycle and native adapters |
| `catalog.py`, `validation.py`, `provenance.py`, `editorial.py` | Catalog models, shared validation, references, version-bound editorial workflow |

Question cancellation invalidates scheduled delivery even if a worker has already
finished. A cancelled network worker keeps its slot until it exits, preventing
new dialogs from starting overlapping requests. Closing/pausing clears key fields
and provider credentials; credentials are never journal data.

Backup format 1 is JSON with `format`, `version`, `created_at`, `payload`, and a
SHA-256 of canonical payload JSON. Payload includes ordered card positions,
discovery identity mappings, voice/unread settings, and archived snapshots with
their original source records and timestamps. Checksums are not signatures;
importing a file is not independent editorial approval. Only restore trusted files.
Size is limited to 32 MiB, 10,000 cards and 20,000 archived versions. Validation
checks all snapshots, supported versions, displayed-fact consistency, identities,
references, positions, and settings before a preview can be confirmed.

Merge retains current cards/settings and appends one snapshot per new organism;
it merges archived history without exact duplicates. Replace restores all saved
card snapshots, including historical duplicates, plus voice/unread settings.
Both modes bind confirmation to the file and current journal fingerprints. Restore
takes a write transaction, checks those fingerprints again, writes/fsyncs a unique
safety JSON copy, then changes tables atomically. Any validation, copy, or SQL failure
leaves the prior collection intact. It sets the migration completion marker, so an
empty restored collection does not re-import an old legacy journal.

Restoration reloads session indexes and refreshes views directly. It never routes
cards through the encounter/narration path. There are no scheduled backups,
background sensing, retries, or automatic provider requests. Local copies are not
off-device protection; export elsewhere before deleting app data. Android's system
document provider can use storage selected by the user, including a connected
cloud provider; VitaDex itself does not upload backups automatically.

Run `python -m pytest`, `python -m ruff check .`, and
`python -m compileall -q *.py vitadex_ui scripts tests`. With a graphical environment,
run `python scripts/check_ui.py --screenshots /tmp/vitadex-ui`. CI uses Xvfb and
checks Python 3.11–3.13. APK checks require the extracted UI modules as well as
catalog/corpus. Android document transfers need actual-device testing; iPhone Files
integration, phone voice/accessibility/energy, and independent human fact approval
are separate open acceptance gates.
