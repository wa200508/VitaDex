#!/usr/bin/env bash
# Run as your normal desktop user after installing the prerequisites in the guide.
set -euo pipefail
if [[ "$(uname -m)" != x86_64 ]]; then
  echo 'This setup is for Intel/AMD x86_64 Ubuntu machines.' >&2
  exit 1
fi
if [[ "$EUID" -eq 0 ]]; then
  echo 'Run this script as your normal user, without sudo.' >&2
  exit 1
fi
sdk_root="${ANDROID_HOME:-$HOME/Android/Sdk}"
export ANDROID_HOME="$sdk_root"
export ANDROID_SDK_ROOT="$sdk_root"
export PATH="$sdk_root/cmdline-tools/latest/bin:$sdk_root/platform-tools:$sdk_root/emulator:$PATH"

if [[ ! -x "$sdk_root/cmdline-tools/latest/bin/sdkmanager" ]]; then
  temp_dir="$(mktemp -d)"
  trap 'rm -rf "$temp_dir"' EXIT
  curl -fL --retry 3 \
    https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip \
    -o "$temp_dir/tools.zip"
  # SHA-256 published at https://developer.android.com/studio#command-tools
  echo "4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583  $temp_dir/tools.zip" | sha256sum -c -
  unzip -q "$temp_dir/tools.zip" -d "$temp_dir"
  mkdir -p "$sdk_root/cmdline-tools"
  if [[ -e "$sdk_root/cmdline-tools/latest" ]]; then
    echo 'Existing cmdline-tools/latest is incomplete; repair it before continuing.' >&2
    exit 1
  fi
  mv "$temp_dir/cmdline-tools" "$sdk_root/cmdline-tools/latest"
fi

# Review and accept licenses interactively; do not pipe automatic acceptance.
sdkmanager --sdk_root="$sdk_root" --licenses
sdkmanager --sdk_root="$sdk_root" \
  'platform-tools' 'emulator' 'system-images;android-35;google_apis;x86_64'
if ! avdmanager list avd -c | grep -Fxq vitadex-test; then
  printf 'no\n' | avdmanager create avd --name vitadex-test \
    --package 'system-images;android-35;google_apis;x86_64' --device pixel_6
fi
emulator -accel-check
echo "Ready. Start the virtual phone with: $sdk_root/emulator/emulator -avd vitadex-test"
