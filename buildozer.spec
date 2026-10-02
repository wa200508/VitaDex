[app]
title = VitaDex
package.name = vitadex
package.domain = org.vitadex
source.dir = .
source.include_exts = py,json,svg,png,jpg,jpeg,kv,atlas,ttf,wav,ogg
source.exclude_dirs = tests,scripts,.git,.github,.pytest_cache,.ruff_cache,__pycache__,models,.venv
source.exclude_patterns = download_models.py
version = 0.1.0
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 0
# The current demo uses no camera, microphone, location, or network permissions.
# Add CAMERA only when capture is implemented with an on-demand permission request.
android.permissions =
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = False

[buildozer]
log_level = 2
warn_on_root = 1
