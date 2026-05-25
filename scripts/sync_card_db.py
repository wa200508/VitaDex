#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen


def download_json(url: str):
    try:
        with urlopen(url) as resp:
            if resp.status != 200:
                raise SystemExit(f'HTTP {resp.status} when fetching {url}')
            return json.load(resp)
    except Exception as e:
        raise SystemExit(f'Failed to download JSON from {url}: {e}')


def validate_against_schema(data, schema_path: Path):
    try:
        import jsonschema
    except ImportError:
        raise SystemExit('Please install jsonschema: pip install jsonschema')

    with schema_path.open('r', encoding='utf-8') as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=data, schema=schema)
    except Exception as e:
        raise SystemExit(f'Validation failed: {e}')


def main():
    parser = argparse.ArgumentParser(description='Fetch a published VitaDex database JSON and validate it against the local schema.')
    parser.add_argument('--url', required=True, help='URL to the published database.json (release asset or raw file).')
    parser.add_argument('--schema', default='card_database_schema.json', help='Local JSON schema path to validate against.')
    parser.add_argument('--output', default='data/database.json', help='Local output path for the downloaded database.')
    args = parser.parse_args()

    schema_path = Path(args.schema)
    if not schema_path.exists():
        raise SystemExit(f'Schema file not found: {schema_path}')

    data = download_json(args.url)
    validate_against_schema(data, schema_path)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'Downloaded and validated database saved to {out_path}')


if __name__ == '__main__':
    main()
