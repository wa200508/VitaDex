# Interface refactor and journal backup

2026-11-03 follow-up. Changes continue on PR #2.

The former 1,017-line `main.py` now launches `VitaDexApp`. Lifecycle/orchestration
lives in `application.py`; screens, reusable widgets/art, and card/question/backup
dialogs live in `vitadex_ui`. Request ownership moved to a headless question
controller with cancellation and stale-delivery tests. Product behavior, source
review gates, saved-card evidence, and first-discovery narration are preserved.
See [the module map](../../ARCHITECTURE.md).

VD-15 now has portable export and previewed merge/replace restore. The format
preserves cards, their citations, discovery IDs, settings, and archived fact
versions. Restores validate first, require an unchanged preview, create a safety
copy, and apply in a transaction. A failed safety copy or interrupted SQL write
does not replace valid saved data. Merges retain existing facts; explicit fact
updates remain a separate review operation. Restoring never narrates cards.

Journal backups exposes local safety copies for preview and export. Android uses
the Storage Access Framework, desktop uses a file chooser. No storage, sensor,
location, or wake-lock permission was added. Only deliberate operations start file
workers; backups do not run on a timer or send API keys anywhere.

Local validation: 115 pytest cases pass, configured Ruff and compilation pass,
and real Kivy checks pass at computer and 360×640 preview sizes. The UI script now
previews and confirms a restore, checks its safety copy, and verifies that neither
restore nor a subsequent familiar encounter requests narration. APK bundle checks
now require the extracted modules. CI and APK runs are required on the pushed head.

Still open: Android transfers through actual document providers (including cancel,
full destination, denied access, app lifecycle/restart), iPhone Files integration,
independent human content approval, real phone audio/accessibility/energy, and
real-provider evaluation. Passing desktop checks does not close these gates.
VD-16 notes/favorites is the next independent feature. It needs stable unread
tracking and a clear rule that removing a visible card does not automatically
forget a species or cause familiar pets to announce again.
