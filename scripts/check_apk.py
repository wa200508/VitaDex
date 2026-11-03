"""Check a built APK's package/permissions and required bundled learning files."""
import argparse
from pathlib import Path
import subprocess
import tarfile
import tempfile
from zipfile import ZipFile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('apk', type=Path)
parser.add_argument('--aapt', required=True)
parser.add_argument('--allow-network', action='store_true', help='Allow the explicitly requested model feature.')
args = parser.parse_args()
permissions = subprocess.run([args.aapt, 'dump', 'permissions', str(args.apk)],
                            check=True, text=True, capture_output=True, timeout=20).stdout
for forbidden in ('CAMERA', 'RECORD_AUDIO', 'WAKE_LOCK', 'ACCESS_FINE_LOCATION') + (() if args.allow_network else ('INTERNET',)):
    if f'android.permission.{forbidden}' in permissions:
        raise SystemExit(f'Unexpected permission in preview: {forbidden}')
with ZipFile(args.apk) as apk:
    archives = [name for name in apk.namelist() if name.startswith('assets/') and 'private' in name]
    found = set()
    for archive in archives:
        with tempfile.TemporaryFile() as stream:
            stream.write(apk.read(archive))
            stream.seek(0)
            try:
                with tarfile.open(fileobj=stream, mode='r:*') as files:
                    found.update(name.lstrip('./') for name in files.getnames())
            except tarfile.TarError:
                continue
    required = {'data/database.json', 'data/corpus.json'}
    if not ({'main.py', 'main.pyc'} & found):
        raise SystemExit('APK is missing its Python entry point.')
    for module in ('application', 'backup', 'questions', 'documents', 'vitadex_ui/screens',
                   'vitadex_ui/dialogs', 'vitadex_ui/questions', 'vitadex_ui/backups', 'vitadex_ui/documents'):
        if not ({module + '.py', module + '.pyc'} & found):
            raise SystemExit(f'APK is missing application module: {module}')
    if not required <= found:
        raise SystemExit(f'APK is missing required bundled files: {sorted(required - found)}')
print('APK checks passed: no sensing or wake-lock permissions; catalog and corpus bundled.')
