[app]
title = VitaDex
package.name = vitadex
package.domain = org.vitadex
source.dir = .
source.include_exts = py,json,svg,png,jpg,jpeg,kv,atlas,ttf,txt,wav,ogg,tflite
source.exclude_dirs = tests,scripts,.git,.github,.codex,.agents,.aws,.pytest_cache,.ruff_cache,__pycache__,.venv,android_src,p4a-recipes,artifacts,tmp,output,docs
source.exclude_patterns = download_models.py
version = 0.1.0
requirements = python3,kivy==2.3.1,filetype,pillow,pyjnius,reportlab==4.4.9,charset-normalizer==3.4.4,chardet==5.2.0
orientation = portrait
fullscreen = 0
# Photo capture requests CAMERA on demand; importing uses the system document picker.
# No microphone, location, network, or broad storage permissions.
android.permissions = CAMERA
android.add_src = android_src
android.extra_manifest_xml = android_src/tts_queries.xml
android.gradle_dependencies = org.tensorflow:tensorflow-lite:2.16.1
p4a.commit = v2024.01.21
p4a.local_recipes = p4a-recipes
android.ndk = 25b
android.sdk_path =
android.skip_update = False
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = False
android.debug_artifact = apk

# Build with: buildozer --profile test android debug
# CI overrides the single ABI and stamps a commit-specific test version.
[app@test]
title = VitaDex Test
package.name = vitadextest
version = 0.0.0-test
android.numeric_version = 1
android.archs = x86_64
android.allow_backup = False

[buildozer]
log_level = 2
warn_on_root = 1
