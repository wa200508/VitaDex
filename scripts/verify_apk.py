#!/usr/bin/env python3
"""Inspect packaged Python extensions before uploading a testing APK."""
import argparse
import io
import struct
import tarfile
from pathlib import Path
from zipfile import ZipFile

MACHINES = {'arm64-v8a': 183, 'x86_64': 62}


def check_elf(raw, name, arch):
    if raw[:4] != b'\x7fELF' or len(raw) < 20:
        raise ValueError(f'{name}: expected an ELF shared library.')
    endian = '<' if raw[5] == 1 else '>'
    machine = struct.unpack(endian + 'H', raw[18:20])[0]
    if machine != MACHINES[arch]:
        raise ValueError(f'{name}: wrong native architecture ({machine}) for {arch}.')
    if b'libc.so.6\x00' in raw or b'GLIBC_' in raw:
        raise ValueError(f'{name}: host Linux/glibc binary cannot be used on Android.')


def verify_apk(path, arch):
    if arch not in MACHINES:
        raise ValueError('Unsupported APK architecture.')
    native_count = 0
    with ZipFile(path) as apk:
        with tarfile.open(fileobj=io.BytesIO(apk.read(f'lib/{arch}/libpybundle.so'))) as bundle:
            names = set(bundle.getnames())
            for required in ('reportlab/pdfgen/canvas.pyc', 'charset_normalizer/md.pyc',
                             'certifi/cacert.pem'):
                if not any(name.endswith('/' + required) for name in names):
                    raise ValueError(f'PDF dependency missing: {required}')
            for member in bundle.getmembers():
                if member.isfile() and member.name.endswith('.so'):
                    check_elf(bundle.extractfile(member).read(), member.name, arch)
                    native_count += 1
                    if '/charset_normalizer/' in member.name:
                        raise ValueError('charset-normalizer must use its pure Python implementation.')
        with tarfile.open(fileobj=io.BytesIO(apk.read('assets/private.tar'))) as private:
            names = set(private.getnames())
            for required in ('print_export.pyc', 'narration.pyc', 'collection_assets.pyc',
                             'catalog_jobs.pyc',
                             'assets/fonts/DejaVuSans.ttf',
                             'assets/fonts/DejaVuSans-Bold.ttf', 'assets/fonts/LICENSE.txt'):
                if required not in names:
                    raise ValueError(f'Print asset missing: {required}')
            if any(name.startswith(('.codex/', '.aws/', 'docs/drafts/')) for name in names):
                raise ValueError('Private development files or editorial drafts were packaged.')
    return native_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('--arch', choices=MACHINES, required=True)
    args = parser.parse_args()
    count = verify_apk(args.apk, args.arch)
    print(f'APK verified: {count} native Python libraries match {args.arch}; PDF assets present.')


if __name__ == '__main__':
    main()
