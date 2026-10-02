[app]
title = VitaDex
package.name = vitadex
package.domain = org.vitadex
source.dir = .
source.include_exts = py,json,svg,png,jpg,jpeg,kv,atlas,ttf,wav,ogg,tflite
source.exclude_dirs = tests,scripts,.git,.github,.pytest_cache,.ruff_cache,__pycache__,.venv,android_src
source.exclude_patterns = download_models.py
version = 0.1.0
requirements = python3,kivy==2.3.1,pillow,pyjnius
orientation = portrait
fullscreen = 0
# Photo capture requests CAMERA on demand; importing uses the system document picker.
# No microphone, location, network, or broad storage permissions.
android.permissions = CAMERA
android.add_src = android_src
android.gradle_dependencies = org.tensorflow:tensorflow-lite:2.16.1
p4a.commit = v2024.01.21
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = False

[buildozer]
log_level = 2
warn_on_root = 1
