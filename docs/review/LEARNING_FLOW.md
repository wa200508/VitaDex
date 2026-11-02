# Learning flow, quality gates, and catalog repair

2026-11-02 follow-up for VD-11–14. Changes continue on PR #2.

- VD-11: saved-card question dialog, offline evidence answers, explicit pending-review
  preview, citation links, optional HTTPS Chat Completions-compatible model passage
  selection, session-only keys, one active worker, cancellation and deliberate speech.
  Provider output cannot introduce displayed prose; only retrieved passage IDs are
  accepted. Actual provider credentials were not used. Richer conversation, native
  non-compatible provider adapters, and persistent secure key storage remain future work.
- VD-12: Python 3.13 added to the quality matrix; all modules compile; a separate
  headless real-Kivy CI job uploads screenshots. The expanded suite has 97 passing
  local tests. The Python 3.11/3.12/3.13 matrix and headless UI job passed on the first learning-flow commit; later refinements rerun the same gates.
- VD-13: reusable catalog module no longer loads a corrupt current bundle on import.
  Sync requires HTTPS (including final redirect), time/payload bounds, complete
  validation, retained latest and content-addressed backups, and atomic replacement.
  Tests cover corrupt-current recovery, timeouts, invalid downloads, and interrupted
  rename. Publishing the matching corpus is an explicit separate operation; stale
  corpus versions fail closed.
- VD-14: names, introductions, and reading controls lead the detail view. Advanced
  review/source data is in a separate popup. Model settings hide in offline mode.
  Child sessions, screen readers, font scaling, safe areas, and actual-device
  ergonomics remain open; a desktop resize check does not close those gates.

Local validation: 97 pytest cases, configured Ruff, compilation, diff checks, and
real Kivy interaction checks pass. UI checks now include separate sources, offline
questions/citations, clearing keys, fact updates, paging, lifecycle, and stale events.
No camera, microphone, passive sensing, automatic model requests, or on-device
illustration generation was introduced.

The prior Android APK build at commit 8ed1a24 completed, passed its permission and
bundle checks, and uploaded a ~21 MB artifact. It predates the Ask interface and
has no Internet permission. Its run is
https://github.com/wa200508/VitaDex/actions/runs/41452080846 . New builds explicitly
allow Internet for the requested model feature; this does not allow camera/audio
capture or wake locks and does not cause background model traffic.

Human source approval and real phone audio/energy validation remain pending.
The next independent feature work is journal backup/restore (VD-15), followed by
personal notes/favorites (VD-16); final art and sensing remain lower priority.
