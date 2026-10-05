#!/usr/bin/env python3
"""Explicit developer update command; never overwrites the bundled/demo catalog."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from catalog_updates import CatalogCache, CatalogUpdateError, update_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, help='Trusted HTTPS manifest URL')
    parser.add_argument('--cache', required=True, type=Path, help='App catalog cache directory')
    args = parser.parse_args()
    try:
        release = update_catalog(args.manifest, CatalogCache(args.cache.resolve()))
    except (CatalogUpdateError, OSError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Installed catalog release {release}. Restart the app to use it.')


if __name__ == '__main__':
    main()
