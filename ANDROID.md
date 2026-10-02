# Android development

Android is the first target platform. The README remains the product specification; the current build is explicitly a fictional-card demo, not a wildlife identification app. See `README_GAP_REPORT.md` for the missing product behavior.

## Build the current demo

Use a Linux development environment with the prerequisites documented by Buildozer and python-for-android (including Java 17, Git, zip/unzip, and native build tools). Install Buildozer in a separate development environment, then run:

```sh
python -m pip install buildozer
buildozer android debug
```

Buildozer downloads the Android SDK/NDK and asks you to accept their licenses. The APK is written to `bin/`. With an Android device connected and USB debugging enabled:

```sh
buildozer android deploy run logcat
```

`buildozer.spec` includes the local JSON catalog and card assets. It intentionally packages only runtime dependencies; Hugging Face and JSON Schema are desktop tooling, not dependencies of the current app. No permissions are declared because the demo uses none. A build configuration is not evidence of a successful APK build or device test.

## Android acceptance criteria for the real field guide

- Implement capture with an explicit user action and runtime camera permission. Denial must leave the card book usable. Stop capture and release resources when the app pauses; do not declare microphone or location permissions for photo identification.
- Choose a mobile identification model and reviewed real-organism catalog with matching identifiers. Bundle or explicitly install model assets, perform bounded inference off the UI thread, and test airplane-mode behavior on a physical device. ComfyUI illustration checkpoints do not constitute an identification model.
- Add optional, user-initiated narration through an offline-capable Android speech engine or bundled audio, with a Stop control and text fallback. Audio capture remains disabled by default.
- Verify Android Back behavior, scrolling, density-aware sizing, large text, TalkBack, touch targets, journal persistence after process termination, and safe handling of denied permissions and model failures.
- Measure inference latency, peak memory, battery use, and APK size on the minimum supported device. Validate the final release target SDK and model/native dependencies against Play requirements before release.
