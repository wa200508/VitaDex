# Mobile preview and device evidence

Android is the provisional first build target because this workspace is Linux;
the user's phone preference has not yet been supplied. This is not a change to
the mobile-only product destination or a claim that iPhone packaging is complete.

## Build and install

The APK job is `.github/workflows/android-preview.yml`. It runs for relevant PR
changes and can be started manually once the workflow is available on the default
branch. A successful job uploads `vitadex-android-preview` as a GitHub Actions
artifact, retained for 14 days. Download the artifact and extract the debug APK.
This is a development preview, not an app-store release.

Pinned inputs: Buildozer 1.6.0, Cython 0.29.36, setuptools 75.8.0, Kivy 2.3.1,
Python/hostpython 3.11.14, python-for-android tag v2026.05.09 at commit
58d21141f17c889bf8585f5665921d72028f8831, NDK 28c, target API 35, minimum API 24,
arm64-v8a, and Temurin JDK 17 on the runner. These pins make changes explicit;
transitive tool downloads/host packages still need recording for a fully locked
release build. Build success must be checked, not inferred from this file.

For a local Linux build, install a **JDK**, not just a Java runtime, plus the host
tools shown in the workflow. In a virtual environment:

```sh
python -m pip install -r requirements-build.txt
buildozer android debug
adb install -r bin/<actual-apk-filename>.apk
adb shell monkey -p org.vitadex.vitadex 1
```

The app bundles its catalog and editorial corpus. Build checks reject missing
files and camera, microphone, location, or wake-lock permissions. Internet permission
is explicitly allowed for the user-requested model feature. The
only manifest addition is TTS service discovery, not permission to record audio.
The preview simulates encounters. Offline question mode makes no model request;
external requests require a configured session and an explicit Send once action.
Android narration rejects voices requiring network access or marked `notInstalled`,
then selects an installed offline English voice or reports that no
usable voice is installed; it does not download one automatically. Other apps or
the OS may still use the network independently.

Use [python-for-android build options](https://python-for-android.readthedocs.io/en/latest/buildoptions.html)
and the [Android TextToSpeech contract](https://developer.android.com/reference/android/speech/tts/TextToSpeech)
when changing packaging or voice handling. iOS requires its own macOS/Xcode build
spike and corresponding audio/device validation; an Android APK does not cover it.

## Current build evidence

The offline Android preview at commit `8ed1a24` successfully compiled, passed its
APK checks, and uploaded the `vitadex-android-preview` artifact at
[run 41452080846](https://github.com/wa200508/VitaDex/actions/runs/41452080846).
This artifact predates the Ask interface and has no Internet permission. Current
builds include the explicitly requested model feature and require a new artifact;
do not treat the older preview as a test of the latest question UI.

The local workspace lacks javac/adb. Successful remote packaging is not evidence
of phone installation, audible speech, interruption handling, or battery use.

## Audio and lifecycle acceptance (VD-08)

Copy `docs/device-results/acceptance-template.json` into ignored `device-results/`
and fill in the actual build, tester, model, OS, voice, observations, and evidence.
Keep every check `not_run` until tested; use `pass` or `fail` only with observations.

1. Start with fresh **test** app data, launch offline, and manually discover Dog.
   Expect a single card and one written/spoken introduction. Do not clear a real
   user's collection for a test.
2. Discover Dog again, restart the app, and repeat. Expect no second automatic
   speech/card; explicit replay must still work.
3. Disable auto voice, discover a different species, then restart. The preference
   persists; the card saves silently. Explicit replay remains deliberate.
4. During replay, use Stop reading. Test Home/background, lock/unlock, resume,
   an audio interruption, headset routing, and application shutdown. Record whether
   playback actually stops, whether a queue unexpectedly resumes, and whether
   native resources are released. Do not mark these passed from a mocked test.
5. Test missing/unavailable offline voice and the offline catalog/journal. Written
   content remains usable and no voice/model/content download starts automatically.
6. Record pronunciation and whether a young child can understand the introduction.

For optional local-only event evidence, with a debuggable installed APK and the
app stopped:

```sh
adb shell run-as org.vitadex.vitadex touch files/diagnostics.enabled
# Launch the app, perform the test, then background/resume or stop normally.
adb shell run-as org.vitadex.vitadex cat files/device-trace.json > device-results/trace.json
adb shell run-as org.vitadex.vitadex rm files/diagnostics.enabled
```

The flag is checked at startup. Diagnostic records are capped at 256, omit spoken
text/questions/notes/credentials, never upload data, and flush only at lifecycle
boundaries. A crash or background clock suspension can leave the final events
unflushed. Re-enable/disable requires restart; do not equate absent events with a
successful cancellation. Normal operation does not enable tracing.

## Energy baseline (VD-09)

Use actual-device platform profiling; the script below is a bounded, read-only
ADB collection aid, not an energy estimator:

```sh
python scripts/device_session.py before --scenario idle --session device-results/idle.json
# Perform a fixed, recorded manual workload; retain the same phone conditions.
python scripts/device_session.py after --session device-results/idle.json
```

Repeat for `browse`, `first-discovery`, `repeat-discovery`, `narration`, and
`background-lock`. Use `--serial` consistently if more than one device is attached.
The commands have timeouts, do not reset device-wide statistics, alter battery
state, acquire wake locks, or claim a result. Record brightness, charging state,
connectivity, battery saver, caches, thermal conditions, workload duration, device,
OS, app build, and voice. Copy the energy-budget template and establish numerical
budgets only after comparable baselines have been measured.

`dumpsys` output varies with Android version and OEM; retain failures as evidence
rather than treating missing diagnostics as a pass. See the official
[dumpsys guide](https://developer.android.com/tools/dumpsys) and
[BATTERY_POLICY.md](BATTERY_POLICY.md). Raw diagnostics may contain device metadata;
keep them local by default. USB charging and wireless ADB both affect measurements
and must be accounted for in the profiling method.
