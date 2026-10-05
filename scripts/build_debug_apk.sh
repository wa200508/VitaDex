#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

arch="${VITADEX_ARCH:-x86_64}"
case "$arch" in
  x86_64|arm64-v8a) ;;
  *) echo 'VITADEX_ARCH must be x86_64 or arm64-v8a' >&2; exit 1 ;;
esac
commit="$(git rev-parse HEAD)"
short_commit="${commit:0:12}"
export APP_ANDROID_ARCHS="$arch"
export APP_VERSION="0.0.0-test.$short_commit"
export APP_ANDROID_NUMERIC_VERSION="${VITADEX_BUILD_NUMBER:-1}"

python download_identification_model.py
python - "$commit" "$arch" <<'PY'
import json
import sys
from pathlib import Path

Path('build_info.json').write_text(json.dumps({
    'channel': 'test', 'commit': sys.argv[1], 'architecture': sys.argv[2],
}, indent=2) + '\n', encoding='utf-8')
PY
buildozer --profile test android debug

# Only distribute an APK from this invocation's test profile/ABI.
apk="bin/vitadextest-$APP_VERSION-$arch-debug.apk"
test -f "$apk"
python scripts/verify_apk.py "$apk" --arch "$arch"
mkdir -p artifacts
destination="artifacts/vitadex-test-$arch-$short_commit.apk"
cp "$apk" "$destination"
cp build_info.json UBUNTU_EMULATOR.md artifacts/
(cd artifacts && sha256sum "$(basename "$destination")" > SHA256SUMS)
echo "Testing APK: $destination"
