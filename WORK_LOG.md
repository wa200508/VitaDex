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
