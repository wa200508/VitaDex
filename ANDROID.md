# Android development

Android is the first target platform. The real-photo flow now suggests broad categories from a 12-entry nature catalog, asks for review, and saves photo cards locally. Fictional sample cards remain available through a separate demo. The README remains the product specification; see `README_GAP_REPORT.md` and `WORK_LOG.md` for remaining work.

## Run on desktop

```sh
python -m pip install -r requirements.txt
python download_identification_model.py
python main.py
```

Use **Scan a Photo → Choose Photo** to exercise the real local model. Desktop inference uses LiteRT; Android uses a native TensorFlow Lite Java bridge. `assets/models/MODEL.md` records the model source, checksum, preprocessing, and limitations.

## Build for Android

For downloadable testing snapshots and an Ubuntu virtual phone, see
[UBUNTU_EMULATOR.md](UBUNTU_EMULATOR.md). The `Android test APK` workflow builds
separate emulator and phone debug APKs on the development branch, without
creating an official release. Use `bash scripts/build_debug_apk.sh` for the
same test build locally.

Use Linux with Java 17 and the native prerequisites documented by Buildozer/python-for-android. In an activated virtual environment, install Buildozer and the supported Cython version, download the model, and build:

```sh
python -m pip install buildozer 'Cython<3'
python download_identification_model.py
buildozer android debug
```

Buildozer downloads SDK/NDK tools and asks for their licenses. The build configuration pins python-for-android to `v2024.01.21` (Python 3.11), Kivy to 2.3.1, and the native TensorFlow Lite dependency to 2.16.1. The APK is written to `bin/`. With a device connected and USB debugging enabled:

```sh
buildozer android deploy run logcat
```

The model binary is ignored by Git but explicitly included by the Android source-extension configuration when downloaded. The runtime has no model download or photo upload code. Hugging Face, JSON Schema, and desktop LiteRT are not Android runtime dependencies. Pillow and a standard-library float array prepare images on Android, avoiding a NumPy build requirement.

The only declared permission is CAMERA, requested when the user chooses **Take Photo**. Import uses Android's system document picker and copies the selected URI into private storage without broad storage permissions. There are no microphone, location, or INTERNET permissions. Imported photos are resized and re-encoded without EXIF/GPS metadata.

## Current verification and build blocker

Desktop tests, real-model inference, narrow-window Kivy rendering, journal persistence, and failed-save recovery pass. Both Java helpers compile against Android API 35 and the declared TensorFlow Lite artifacts; the PyJNIus byte/float bridge was checked with a desktop JVM.

The earlier full APK attempt stopped while downloading FreeType 2.10.1:
`download.savannah.gnu.org` returned HTTP 403. A local recipe now uses FreeType's
official SourceForge mirror with a verified SHA-256, retaining the pinned recipe
and version. GitHub Actions successfully produced both x86_64 and arm64-v8a
debug APKs for commit `af86b8b`; the emulator download's checksum, bundled model,
test identity, and debug manifest were inspected. Emulator/device execution
still needs verification. See `WORK_LOG.md` for the build handoff.

## Required Android device checks

- Verify the native model and JPEG/PNG decoding with real photos in airplane mode; expand validation beyond the small starter catalog.
- Test the system document picker on recent scoped-storage devices, cancellation, inaccessible URIs, and size limits.
- Test camera permission denial and revocation, preview orientation, capture quality, repeated capture, and resource release when paused or dismissed. The Kivy 2.3.1 Android provider requires explicit hardware release after stopping its preview; this path needs device testing.
- Verify Android Back, large text, density-aware touch targets, TalkBack, process termination, journal migrations, and failed storage writes. Cancelled/rejected scans must leave no new card.
- Measure latency, peak memory, battery, APK size, and native-library support on the minimum supported device. Review the pinned toolchain, target SDK, and 16 KB page-size compatibility before release.
- Add user-initiated local narration with Stop controls and text fallback, child-friendly settings, and reviewed factual content. Optional microphone capture remains unimplemented and permission-free by default.
