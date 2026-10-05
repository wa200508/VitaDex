#!/usr/bin/env python3
"""Build immutable publication files locally after recorded scientific review."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from catalog_updates import MAX_BUNDLE_BYTES, decode_bundle


def publish(catalog, reviews, release, output):
    raw = json.dumps(dict(schema_version=1, release=release, catalog=catalog,
                          reviews=reviews), ensure_ascii=False, sort_keys=True).encode('utf-8')
    decode_bundle(raw)
    if len(raw) > MAX_BUNDLE_BYTES:
        raise ValueError('Publication exceeds the app size limit.')
    digest = hashlib.sha256(raw).hexdigest()
    name = f'catalog-{release}-{digest}.json'
    output.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental replacement of immutable publications.
    with (output / name).open('xb') as stream:
        stream.write(raw)
    manifest = dict(schema_version=1, release=release, bundle=name, size=len(raw), sha256=digest)
    temporary = output / 'manifest.json.tmp'
    temporary.write_text(json.dumps(manifest, indent=2) + '\n')
    temporary.replace(output / 'manifest.json')
    return output / 'manifest.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--reviews', type=Path, required=True)
    parser.add_argument('--release', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(publish(json.loads(args.catalog.read_text()), json.loads(args.reviews.read_text()),
                  args.release, args.output))


if __name__ == '__main__':
    main()
