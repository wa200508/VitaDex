# VitaDex testing on Ubuntu

These downloads are development snapshots, not official releases. The app is
named **VitaDex Test**, uses the separate package `org.vitadex.vitadextest`, and
shows the source commit on its home screen. Its journal is separate from VitaDex.
No release tags or GitHub Releases are created by the testing workflow.

## Get the test APK

1. Sign into GitHub and open [Android test APK workflow runs](https://github.com/wa200508/vitadex/actions/workflows/android-debug.yml).
2. Open a successful run for `development/readme-android`.
3. Download the `vitadex-test-x86_64-<commit>` artifact for the Ubuntu emulator.
   The `arm64-v8a` artifact is for a physical Android phone.
4. Extract the ZIP. It contains the debug APK, `SHA256SUMS`, build identity, and
   this guide. Run `sha256sum -c SHA256SUMS` from the extracted directory.

Builds run on pushes to the development branch; artifacts expire after 30 days.
GitHub requires the workflow on the default branch before its manual **Run
workflow** button is available. Branch pushes work without merging into main.
The first build may take a substantial amount of time downloading and compiling
the native toolchain. A failed run has no downloadable APK.
CI uses an isolated SDK with Build Tools 35.0.0 and Command-Line Tools 12.0,
then disables Buildozer's automatic SDK updates to retain toolchain compatibility.

## Install the emulator

For an Intel/AMD 64-bit Ubuntu desktop with hardware virtualization enabled in
BIOS/UEFI. Allow several GB for the SDK and virtual phone. Android Studio is
optional; these commands install Google's emulator and command-line tools.

Install prerequisites:

```sh
sudo apt update
sudo apt install -y openjdk-21-jdk curl unzip qemu-kvm \
  libgl1 libpulse0 libnss3 libx11-6 libxcb1 libxcomposite1 libxcursor1 \
  libxi6 libxtst6 libxrandr2 libxkbcommon0 libxkbcommon-x11-0
sudo usermod -aG kvm "$USER"
```

**Log out and back in** so your KVM group membership takes effect. Then, from
the repository's `development/readme-android` branch:

```sh
bash scripts/setup_ubuntu_emulator.sh
```

The script downloads checksum-verified Google SDK tools into `~/Android/Sdk`
(or your existing `ANDROID_HOME`), asks you to review SDK licenses, downloads an
Android 15/API 35 x86_64 image, creates `vitadex-test`, and checks acceleration.
Run it without sudo. If multiple Java versions are installed, select Java 21
for these tools with `sudo update-alternatives --config java`.

Set paths in each terminal where you use the emulator:

```sh
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
emulator -avd vitadex-test
```

Leave the emulator running. In another terminal, set the paths above and install
the extracted APK (replace the filename with your download):

```sh
adb -e wait-for-device
adb -e install -r ./vitadex-test-x86_64-<commit>.apk
adb -e shell monkey -p org.vitadex.vitadextest -c android.intent.category.LAUNCHER 1
```

You can also drag the APK onto the virtual phone to install it. Drag a JPEG or
PNG onto it to copy a test photo into Downloads, then use **Scan a Photo → Choose
Photo**. Try the fictional demo, card details, Back navigation, and restarting
the app to check persistence. Suggestions remain unverified.

Debug signing keys may differ between clean CI runs. If an update reports
`INSTALL_FAILED_UPDATE_INCOMPATIBLE`, uninstall the old test app and reinstall:
`adb -e uninstall org.vitadex.vitadextest`. **Uninstalling deletes its test journal
and photos.** Do this only when you are ready to discard that test data.

## Troubleshooting

- Run `emulator -accel-check`, `ls -l /dev/kvm`, and `id` if KVM is unavailable.
  Enable CPU virtualization and check that your login belongs to `kvm`.
- For graphics failures try `emulator -avd vitadex-test -gpu swiftshader`.
- For crashes run `adb -e logcat -s python AndroidRuntime`.
- `INSTALL_FAILED_NO_MATCHING_ABIS` means you downloaded the phone APK; use
  `x86_64` for this emulator.
- The emulator supports UI and functional testing; camera quality, battery
  usage, and physical-device behavior still need testing on real hardware.

## Build locally instead

Use the Linux build prerequisites in `ANDROID.md`, a Python 3.11 virtual
environment, and Java 17 for the pinned Android build toolchain (the emulator
tools above use Java 21):

```sh
python -m pip install buildozer==1.6.0 Cython==0.29.37 setuptools==70.3.0
bash scripts/build_debug_apk.sh
```

The default ABI is `x86_64`; set `VITADEX_ARCH=arm64-v8a` for a phone. Buildozer
prompts for licenses locally. Outputs go to `artifacts/`. The model is downloaded
and checksum-verified before packaging. The FreeType recipe keeps version 2.10.1
and uses its official SourceForge mirror with a pinned SHA-256 to avoid the
previous Savannah HTTP 403. The remaining pinned recipes are unchanged.

References: [Google SDK tools](https://developer.android.com/studio#command-tools),
[sdkmanager](https://developer.android.com/tools/sdkmanager),
[avdmanager](https://developer.android.com/tools/avdmanager),
[Linux acceleration](https://developer.android.com/studio/run/emulator-acceleration#vm-linux),
[APK installation](https://developer.android.com/studio/run/emulator-install-add-files).
