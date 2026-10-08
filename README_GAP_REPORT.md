# Implementation status against the README

The README remains the product specification. Android is the first target platform. This report records actual implementation and verification, without treating desktop checks as Android-device validation.

## Implemented

- Transactional offline catalog cache, validated publication/update commands, same-origin
  bounded HTTPS downloads, checksum and rollback checks, and previous-release recovery.
  Startup has no network access. Public GitHub-hosted files and an explicit Android update button are implemented; no background polling is enabled.
- Local cartoon artwork with original-photo choice, fact review/citation metadata,
  source-constrained future discussion hooks, and an offline topic-based field guide.
- Single-card Letter/A4 PDF front/back export with cut marks, bleed, embedded fonts,
  full fact/reference appendix and Android system document save integration.
- A separate four-organism source-cited draft prepared for human review. It is not part
  of the active catalog and is not approved for scientific publication.

- Kivy navigation, a persistent SQLite card journal, and a clearly separate fictional demo. Random sample selection no longer claims to be a real scan or reports 100% confidence.
- Real photo input, local EfficientNet-Lite0 inference, and a 12-category nature catalog with stable IDs, taxonomic names, safety guidance, and reference links.
- Conservative result gating: the global winning model label must be supported; ambiguous and low-scoring output does not create a card. Suggestions require review before saving and remain labeled unverified afterward.
- One background scan at a time, UI-thread delivery, cancellation on navigation/pause, and removal of owned photos after rejection, cancellation, provider failure, or discarded review.
- Private resized photo copies with EXIF/GPS removed; photo rendering and selected background colors on collectible cards.
- Encounter IDs, UTC recording timestamps, photo references, model source, and score persisted in journal version 2. Existing version-1 SQLite/JSON snapshots remain readable and migrate without losing their content.
- Journal protection: unreadable collections are kept unchanged, failures are visible, and only durable saves appear in the collection. Popups restore the prior popup after nested errors, supporting Back-button recovery.
- Scrollable/wrapped descriptions and details, responsive card-grid columns, stacked collection controls, explicit dismissal controls, and Android Back handling.
- Android build configuration and Java helpers for local inference and private document-URI copying. CAMERA is requested on demand; INTERNET is declared for explicit catalog downloads; document import needs no broad storage permission. The camera is stopped/released on dismissal and pause.
- A public, pinned identification-model downloader with SHA-256 verification and atomic installation. Getting Started now uses this runnable setup; the product goals in the README remain intact.

## Remaining work

| Priority | Requirement | What remains |
| --- | --- | --- |
| 1 | Verified Android application | Debug APK packaging now succeeds for x86_64 emulators and arm64-v8a phones. Test startup and UI in the emulator, then native inference, camera, document picker, permissions, and lifecycle on a physical Android device. Packaging alone does not prove the app runs. |
| 1 | Reliable nature identification | The general ImageNet model only suggests broad categories. Expand specialist-model and geographic validation, test unknown/unsupported input, and measure false confident matches. Never interpret scores as calibrated species certainty or edibility/safety advice. |
| 1 | Reviewed nature catalog | The starter catalog has factual summaries and references but needs independent content review, broader coverage, and explicit model/taxon compatibility. Keep fictional snapshots marked separately. |
| 2 | Audio descriptions | User-initiated Android narration and Stop controls are implemented with installed offline English voices. Test engine availability, audio settings and lifecycle on devices. Microphone capture remains absent. |
| 2 | Child-friendly controls and accessibility | Implement the intended settings/parent-control flow; convert remaining raw pixel sizing to density-aware units; test large text, TalkBack, touch targets, keyboard focus, and contrast on devices. |
| 2 | Personal artwork | Lightweight Pillow filtering now creates private cartoon-style art after recognition. Evaluate visual quality and battery cost on device; artwork changes for saved cards are implemented. ComfyUI is no longer required for the core experience. |
| 3 | Battery, latency, and memory goals | Inference is local and bounded to one job/two native threads. Measure it on target Android devices, along with camera resources and APK size; desktop latency is not a battery benchmark. |
| 3 | Complete journal lifecycle | Single-card print export is implemented. Confirmed deletion and aged orphan-photo cleanup are implemented. Add backup behavior and decide whether unread status and display ordering should persist. Verify atomic behavior under device storage failures. |
| 3 | Release readiness | Review model distribution terms, pinned native/toolchain versions, SDK/Play requirements, and 16 KB native page-size compatibility before release. |

## Validation

The latest local check passed 109 tests, Ruff, and Python compilation on Python 3.12. Tests cover catalog/schema invariants, conservative model output handling, real downloaded-model inference, label alignment, model-download integrity, private photo handling, scan cancellation/failure/shutdown, journal protections, version-1 migration, transactional catalog updates, PDF output/overflow/failure behavior, and document-picker callback handling.

A Kivy flow rendered at phone-sized windows and exercised a real photo, suggested-match review, simulated disk-full recovery, persistence, separate fictional samples, and Back navigation. Native Java helpers compiled against Android API 35/TensorFlow Lite 2.16.1, and a PyJNIus byte/float round trip passed. A small real-flower corpus check demonstrates category breadth, not species accuracy. Details and restart instructions are in `WORK_LOG.md`.

On October 3, 2026 (America/New_York), GitHub Actions built x86_64 and arm64-v8a
debug APKs for `af86b8b`; Python 3.11/3.12 CI passed. The downloaded emulator APK
passed checksum and packaged-model verification, and its manifest confirms
`VitaDex Test`, `org.vitadex.vitadextest`, debug mode, and CAMERA as its only
permission. The native build succeeds with the checksum-pinned FreeType mirror.
No emulator or physical-device runtime test has been performed in this session.
