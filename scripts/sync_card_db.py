#!/usr/bin/env python3
"""Bounded, validated, atomic catalog replacement with a retained previous file."""
import argparse
import json
from hashlib import sha256
import os
from pathlib import Path
import sys
import tempfile
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from catalog import CardDatabase

MAX_BYTES = 5 * 1024 * 1024


def download_json(url, timeout=15):
    if not url.startswith('https://'):
        raise ValueError('Catalog downloads require HTTPS.')
    with urlopen(url, timeout=timeout) as response:
        if not response.geturl().startswith('https://'):
            raise ValueError('Catalog redirect downgraded HTTPS.')
        if response.status != 200:
            raise ValueError(f'Catalog download returned HTTP {response.status}.')
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Catalog exceeds the 5 MiB limit.')
        return json.loads(raw)


def validate_against_schema(data, schema_path):
    import jsonschema
    jsonschema.validate(data, json.loads(Path(schema_path).read_text()))
    CardDatabase.from_json(data)


def atomic_bytes(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile('wb', dir=path.parent, delete=False) as output:
            name = output.name
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()


def sync_catalog(url, output, schema_path, timeout=15):
    data = download_json(url, timeout)
    validate_against_schema(data, schema_path)
    output = Path(output)
    content = (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode()
    if output.exists():
        previous = output.read_bytes()
        archive = output.with_name(output.name + '.bak.' + sha256(previous).hexdigest()[:16])
        if not archive.exists():
            atomic_bytes(archive, previous)
        atomic_bytes(output.with_name(output.name + '.bak'), previous)
    atomic_bytes(output, content)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--schema', type=Path, default=Path(__file__).resolve().parents[1] / 'card_database_schema.json')
    parser.add_argument('--output', type=Path, default=Path('data/database.json'))
    parser.add_argument('--timeout', type=float, default=15)
    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error('Timeout must be greater than 0 and no more than 60 seconds.')
    try:
        sync_catalog(args.url, args.output, args.schema, args.timeout)
    except Exception as error:
        raise SystemExit(f'Catalog update failed; the target was not partially written: {type(error).__name__}: {error}')
    print(f'Validated catalog saved to {args.output}; prior bytes retained as .bak. Rebuild the corpus before publication.')


if __name__ == '__main__':
    main()
