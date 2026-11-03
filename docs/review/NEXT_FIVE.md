# VD-06 through VD-10 implementation follow-up

Updated 2026-11-02. Code and tooling are implemented; several acceptance conditions
require people or real phones and have not been fabricated.

| Item | Implemented | Still required |
| --- | --- | --- |
| VD-06 editorial review | Exact-version pending packets, human declarations/checks, stale/altered-record rejection, separate proposed catalog output, explicit saved-card update preview and archived originals | Independent human review of facts, source mapping, reuse terms, and reading clarity |
| VD-07 mobile preview | Provisional Android arm64 build spec, pinned tools, offline assets, TTS queries, permission/content checks, GitHub APK artifact job | Successful APK build/install evidence; phone target preference; iOS build if selected |
| VD-08 phone audio/lifecycle | Offline-only Android voice selection, bounded opt-in local trace, unfilled result template, reproducible real-device steps | Actual audio/routing/stop/pause/lock/interruption/offline observations |
| VD-09 energy baseline | Read-only, timeout-bounded before/after ADB diagnostics, scenario metadata, unfilled budget template | Real-device profiler runs, controlled baselines, and numerical budgets based on measurements |
| VD-10 permitted evidence | Offline editorial-summary passages for all five organisms, source/content versions, hashes, attribution/reuse basis, scoped lexical retrieval, evaluation cases, saved-snapshot context | Human approval; larger licensed primary-source text if broader question coverage is desired; model/chat integration is VD-11 |

## Verification

- **83 tests pass**, including review packet integrity, corpus versions and unsupported
  questions, archived source updates (including older snapshots without IDs),
  diagnostic opt-in/data minimization/write errors, and existing regression checks.
- Configured lint, compilation, and diff checks pass.
- Real Kivy script passes existing interaction checks plus an explicit fact update
  that preserves collection count and does not request another spoken discovery.
- Build requirements resolve after correcting the Cython pin to the range required
  by Buildozer. No camera/microphone/network or model use was added to the preview.

## Build evidence

Local `buildozer android debug` stopped at the missing Java compiler (`javac`),
not an application test. The workspace also lacks adb and therefore cannot supply
phone evidence. No device template has a completed result or energy limit.

The initial remote build failed during pip installation because Cython 3.0.12
conflicted with Buildozer 1.6.0's Cython<3 requirement. It was corrected to 0.29.36
and a dependency-resolution dry run passed. Regular GitHub CI passed. The
replacement Android build is being monitored at
[run 41449912872](https://github.com/wa200508/VitaDex/actions/runs/41449912872).
Its compilation step succeeded, but the older output checker required `main.py`
instead of accepting the compiled `main.pyc`. The checker was corrected in the
next build. A running job is not evidence of a verified artifact; record its final result before
claiming an installable artifact.

See [MOBILE_PREVIEW.md](../../MOBILE_PREVIEW.md),
[EDITORIAL_REVIEW.md](../../EDITORIAL_REVIEW.md), and
[CORPUS.md](../../CORPUS.md) for reproducible use and explicit limitations.
