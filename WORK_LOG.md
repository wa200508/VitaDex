# VitaDex restart handoff — 2026-10-02 UTC

## Decisions and repository state

- The README is the product specification. Preserve its nature-discovery, local-processing, child-safety, accessibility, and collectible-journal goals.
- Android is the first target platform. Use the sandbox for substantial builds/tests when useful.
- Work on `development/readme-android`, commit changes, and push to the development branch. Do not merge into main without a separate instruction.
- Origin is `ssh://git@ssh.github.com:443/wa200508/VitaDex.git`. The user's forwarded SSH key now authenticates successfully as `wa200508`; HTTPS `GH_TOKEN` was invalid. No credentials are stored in the repository.
- Earlier pushed commits: `b350820` (journal protections), `1b58323` (honest demo/safety/layouts), and `4031ad0` (initial Android configuration/gap report).
- Latest implementation commit: `67bbbc8` — Add local photo suggestions and persistent encounter cards. This log, updated setup instructions, and updated implementation report accompany it in the following documentation commit.

## Completed work

The initial audit found that Scan randomly selected one of three fictional organisms, reported full confidence, displayed placeholder art strings, had no camera/model/audio integration, and directed users to a nonexistent ComfyUI workflow. An unreadable journal could be mistaken for an empty collection and overwritten, while failed saves still appeared successful.

Those immediate defects were corrected: fictional samples are explicitly labeled and kept in a separate demo; safe observation guidance is visible; failed loads prevent writes; cards appear only after durable saves; descriptions scroll/wrap; narrow layouts have responsive card columns and stacked controls; popups have visible dismissal controls and Android Back behavior.

The next implementation adds:

- Real-photo scanning backed by a pinned EfficientNet-Lite0 TensorFlow Lite model. Desktop uses LiteRT; Android has a Java/PyJNIus CPU interpreter bridge. Models are loaded locally, with two native threads and no runtime network calls.
- A separate 12-category nature catalog: ladybird beetle, bee, ant, grasshopper, mantis, dragonfly, damselfly, monarch butterfly, cabbage white group, snail, slug, and daisy-like flower. Entries include stable IDs, taxonomic names, safety messages, and reference URLs. Independent content review remains needed.
- Conservative model gating. Unsupported global winners are rejected rather than replaced by a lower-ranked nature label. Ambiguous/low-scoring output does not create cards. A supported suggestion must be reviewed before saving, and remains labeled unverified in the journal.
- Photo import and camera-preview flows. Android import uses ACTION_OPEN_DOCUMENT and a bounded private URI copy. Only CAMERA is declared/requested, on demand; there are no microphone, location, INTERNET, or broad storage permissions. Native input flows still need device verification.
- Private, resized JPEG copies with orientation applied and source EXIF/GPS removed. Cards render those photos and selected background colors.
- A single background scan worker with scheduled UI delivery, duplicate-request prevention, cancellation on leaving/pausing, and private-photo cleanup on rejected/discarded/failed/cancelled scans. Shutdown discards running results.
- Journal version 2 with encounter IDs, UTC recording time, photo references, source, and raw model score. Version-1 SQLite/JSON snapshots migrate without losing existing cards; old fictional content stays marked as demo.
- A checksum-verified, atomic public-model installer and checked-in label order. The roughly 18.6 MB model binary is ignored by Git and must be downloaded before launch/build. It is included in Android packaging through the `.tflite` extension.
- CI now installs the local model and exercises real inference/label alignment alongside regressions. Python code, native helpers, model metadata, and source configuration are committed.

## Verification completed

- **53 tests passed** on Python 3.12, including the actual downloaded model. Ruff, Python compilation, and `git diff --check` passed.
- Tests cover model output bounds/ambiguity/unsupported classes, label alignment, download integrity/idempotence/cleanup, EXIF removal, image limits/orientation, scan failure/cancellation/shutdown, journal failures, durable additions, and version-1 migration.
- Kivy rendered at phone-sized windows, including 320×568 and 360×640. A real daisy photo passed inference and review, simulated disk-full failure left the collection unchanged, Back restored the review popup, retry saved the card/photo, and reload preserved it. Separate fictional-demo creation also passed.
- Both Java helpers compiled against Android API 35 and TensorFlow Lite/API 2.16.1 artifacts. A desktop PyJNIus byte-buffer/float round trip passed. This does not prove native Android execution.
- An exploratory 150-photo TensorFlow flower-dataset check produced daisy-like suggestions for 23/30 daisies, 11/30 sunflowers, 2/30 dandelions, and 0/30 roses or tulips. These are suggestion counts, not validated species accuracy. They motivated broad category labeling. Timing in that exploratory report predates the final standard-library Android preprocessing path; remeasure before making performance claims.

## Android build attempt and blocker

Buildozer 1.6.0 and build prerequisites were installed in the sandbox, including Java 17, Ant, native compilers/build tools, Xvfb, and OpenGL libraries. SDK API 35 and NDK r25b were installed/cached. The build configuration pins python-for-android to `v2024.01.21` (Python 3.11), Kivy 2.3.1, and native TensorFlow Lite 2.16.1. Preprocessing accommodates the pinned toolchain's older Pillow API.

The full APK build reached native recipe downloads, then failed fetching **FreeType 2.10.1** from `https://download.savannah.gnu.org/releases/freetype/freetype-2.10.1.tar.gz` with HTTP 403 after retries. No APK was produced. There are no ongoing build jobs to resume automatically.

Useful sandbox artifacts (not committed; may disappear across sandbox/system recreation):

- Test/development environment: `/tmp/vitadex-check` (Python 3.12).
- Build log: `/tmp/vitadex-android-build.log`. Buildozer logs may contain environment diagnostics; do not publish the full log without reviewing it.
- Build cache: workspace `.buildozer/`; SDK/NDK cache under `/home/agent/.buildozer/android/platform/`.
- Installed local model: `assets/models/efficientnet_lite0.tflite` (ignored by Git).
- Exploratory image dataset: `/tmp/vitadex-flower-photos/flower_photos/`; summary `/tmp/vitadex-model-validation.json`.
- Rendered review screenshot: `/tmp/vitadex-review-render0001.png`.
- Native compile artifacts: `/tmp/vitadex-java-check/`.

## Next work, in order

1. Resolve the trusted FreeType dependency download/cache or update to a compatible supported Android toolchain. Complete the APK build. Avoid claiming Android readiness from desktop tests or Java compilation.
2. Test on a physical Android device: document URI import, camera denial/revocation, preview orientation/quality, repeated capture, pause/resume/resource release, Back navigation, private storage, and native inference in airplane mode.
3. Expand catalog/content review and model validation. The current ImageNet model is a category suggester with limited coverage and potentially confident mistakes. Choose/evaluate a specialist mobile nature model before claiming dependable species identification. Keep scores distinct from calibrated certainty.
4. Implement user-initiated offline narration with Stop and text fallback. Add child-friendly settings and validate TalkBack, large text, density-aware sizing, keyboard focus, and contrast.
5. Complete artwork/ComfyUI integration if retained: real workflow, standard API parsing, checkpoint-to-repository mappings, downloads/token handling, and rendering. `download_models.py` remains separate/incomplete; it is not the new identification-model installer. The SVG background template is still unused.
6. Add journal export/deletion/backup, orphaned-photo cleanup after abrupt process death, and decide whether unread state/order should persist. Measure Android latency, memory, battery, and APK size. Review pinned native versions, model distribution terms, target SDK, and 16 KB page-size support before release.

## Resume commands

```sh
git switch development/readme-android
git pull --ff-only
python -m pip install -r requirements-dev.txt
python download_identification_model.py
python -m pytest
python -m ruff check .
python main.py
```

If the cached test environment exists, use `/tmp/vitadex-check/bin/python` for the Python commands. Android build/device instructions are in `ANDROID.md`; model details are in `assets/models/MODEL.md`; the current requirement-by-requirement status is in `README_GAP_REPORT.md`.

## Testing APK handoff — October 3, 2026 (America/New_York)

- Commits `c1eb748` and `af86b8b` add the `Android test APK` workflow, a separate
  Buildozer test profile, build identity, and an optional Ubuntu emulator setup
  script. No emulator installation was run. No release or tag was created, and
  main was not changed.
- Both debug APKs built successfully in
  [workflow run 37167263231](https://github.com/wa200508/VitaDex/actions/runs/37167263231).
  Choose `x86_64` for the Ubuntu emulator, `arm64-v8a` for a phone. Artifacts
  contain the APK, SHA256SUMS, build identity, and Ubuntu guide; retention is 30 days.
- The app is named VitaDex Test, uses `org.vitadex.vitadextest`, shows its source
  commit, and has a separate journal. Debug signing keys may change between
  clean builds; see the guide before uninstalling an older test app.
- FreeType 2.10.1 now uses the official SourceForge mirror. Its archive was
  downloaded and matched Buildroot's published SHA-256. CI uses an isolated
  SDK with Command-Line Tools 12.0, Build Tools 35.0.0, Java 17, NDK r25b, and
  the existing pinned p4a version. Kivy 2.3.1's filetype dependency is explicit.
- Local checks passed all 53 tests with the downloaded real model, Ruff, Python
  compilation, shell syntax, and actionlint. GitHub Python 3.11/3.12 CI passed.
- The downloaded x86_64 bundle passed APK checksum, x86_64 runtime and packaged
  model checks. Its manifest confirms the test name/package, debug flag, and
  CAMERA as the only permission. Local Codex/agent/Git directories are excluded.
- Remaining: actually launch and exercise the APK in an emulator, then test
  native inference and physical-device camera/import/lifecycle behavior. The
  earlier FreeType blocker is resolved; the other model/content/accessibility
  gaps remain. Ubuntu commands are in `UBUNTU_EMULATOR.md`.

## Offline catalog foundation and personal artwork (2026-10-04)

- Added `docs/OFFLINE_CATALOG.md`: editorial PostgreSQL, immutable CDN catalog
  publications, constrained Android background updates, source-level scientific review,
  private encounter snapshots, broad taxonomy support, and offline PDF export design.
- Added draft/review metadata and a publication validator requiring per-field citations
  and independent approval of the exact revision. Existing entries remain drafts.
- Generate bounded local median-filtered/posterized artwork after recognition on the
  existing worker; choose original/artwork in review and persist the choice separately
  from the original photo and catalog facts. Cancelled encounters discard both files.
- Replaced animal-centric general UI wording with living things/organisms.
- Hosting, update scheduling, scientifically reviewed content and printable PDF output
  remain subsequent milestones, explicitly documented rather than advertised as live.
- Validation: 60 tests passed, including real local-model inference; Ruff, Python
  compilation and diff whitespace checks passed. No emulator/device run performed.

## Field-guide interaction and future discussion hooks (2026-10-04)

- Added automatic catalog introduction in card detail and an offline “Explore this
  organism” view with fixed topic questions and source display.
- Added immutable reviewed evidence requests and optional discussion/narration protocols.
  The discussion boundary renders stored passages only, rejects invented evidence IDs,
  and refuses draft/fictional/uncited material. No AI or speech provider is enabled.
- Documented automatic encounter logging as dependent on recognition validation, device
  TTS, optional local/cloud adapters, consent boundaries and grounding limitations.
  Current suggestions retain Save/Discard; AI remains the final delivery priority.
- Validation: all 69 tests passed (including local-model inference); Ruff, compilation
  and diff checks passed. The new Kivy screen has not been tested in an emulator/device.

## Safe catalog storage and printable cards (2026-10-04)

- Implemented bounded HTTPS manifest/bundle downloads, same-origin/no-redirect policy,
  checksums, publication validation, rollback rejection, and transactional two-release
  SQLite storage. Startup reads only the local cache with previous/bundled fallback.
- Added immutable publication and explicit updater commands; retired direct overwrites
  of the bundled database. New unsupported recognition labels no longer prevent startup.
- Added offline Letter/A4 PDF export from saved cards with matched front/back pages,
  2.5 x 3.5 inch trim, bleed/cut marks, embedded fonts and complete facts/references.
  Android uses a document destination picker; PDF work and writes run off the UI thread.
- Added a pinned pure-Python ReportLab Android recipe, avoiding the legacy native recipe.
- Validation: 83 tests passed, Ruff/compile/diff checks passed; rendered the three-page
  Letter proof and inspected each page. Android builds and device save/print checks
  remain to be verified. No hosting endpoint or scientific approvals were fabricated.
