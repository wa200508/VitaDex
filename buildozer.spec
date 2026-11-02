[app]
title = VitaDex Preview
package.name = vitadex
package.domain = org.vitadex
source.dir = .
source.include_exts = py,json,png,kv,atlas,xml
source.exclude_dirs = tests,scripts,docs,.git,.github,.pytest_cache,.ruff_cache,.buildozer,bin
source.exclude_patterns = data/editorial/*,data/demo_database.json
version = 0.2.0
requirements = python3==3.11.14,hostpython3==3.11.14,kivy==2.3.1,sqlite3,pyjnius
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.ndk = 28c
android.ndk_api = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions =
android.extra_manifest_xml = mobile/android/queries.xml
p4a.branch = v2026.05.09
p4a.commit = 58d21141f17c889bf8585f5665921d72028f8831
p4a.bootstrap = sdl2
p4a.setup_py = false

[buildozer]
log_level = 2
warn_on_root = 1
