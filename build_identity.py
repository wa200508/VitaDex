"""Display the identity stamped into a testing APK, without runtime Git access."""

import json
from pathlib import Path


def build_identity():
    path = Path(__file__).with_name('build_info.json')
    if not path.is_file():
        return 'VitaDex', None
    info = json.loads(path.read_text(encoding='utf-8'))
    return 'VitaDex Test', f'Testing build · {info["commit"][:12]}'
