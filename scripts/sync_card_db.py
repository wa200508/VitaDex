#!/usr/bin/env python3
"""Compatibility entry point for the safe catalog updater.

The former direct overwrite of data/database.json has been retired. Use a trusted
--manifest and an explicit --cache; demo and bundled catalogs remain unchanged.
"""
from update_catalog import main

if __name__ == '__main__':
    main()
