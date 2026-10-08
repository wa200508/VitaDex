#!/usr/bin/env python3
"""Prepare public files from reviewed inputs; never turn drafts into approvals."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.publish_catalog import publish
from catalog_updates import decode_bundle


PENDING = dict(schema_version=1, status='awaiting_review')


def prepare(source, output):
    paths = [source / name for name in ('catalog.json', 'reviews.json', 'release.json')]
    manifest = output / 'manifest.json'
    if not any(path.exists() for path in paths):
        if manifest.exists():
            return manifest  # Removing input files never withdraws an existing publication.
        output.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(PENDING, indent=2) + '\n')
        return manifest
    if not all(path.is_file() for path in paths):
        raise ValueError('Reviewed catalog, review records and release.json must all be present.')
    catalog, reviews, metadata = [json.loads(path.read_text()) for path in paths]
    release = metadata['release']
    raw = json.dumps(dict(schema_version=1, release=release, catalog=catalog,
                          reviews=reviews), ensure_ascii=False, sort_keys=True).encode('utf-8')
    decode_bundle(raw)
    if manifest.exists():
        existing = json.loads(manifest.read_text())
        old_release = existing.get('release', 0)
        if release == old_release:
            # A workflow retry is harmless only when the exact immutable file still exists.
            name = existing['bundle']
            if Path(name).name != name or (output / name).read_bytes() != raw:
                raise ValueError('This publication number already has different content.')
            return manifest
        if release < old_release:
            raise ValueError('Use a strictly newer publication number.')
    return publish(catalog, reviews, release, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.source, args.output))


if __name__ == '__main__':
    main()
