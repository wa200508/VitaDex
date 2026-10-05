"""Bounded explicit catalog downloads and transactional offline snapshots.

Importing or loading the cache performs no network access. The trusted HTTPS
manifest endpoint is supplied by deployment configuration, never by catalog text.
"""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, build_opener

from catalog_review import validate_publication
from database import CardDatabase

MAX_BUNDLE_BYTES = 8 * 1024 * 1024
MAX_MANIFEST_BYTES = 8192
SCHEMA_VERSION = 1


class CatalogUpdateError(ValueError):
    pass


def decode_bundle(raw):
    try:
        data = json.loads(raw)
        if data['schema_version'] != SCHEMA_VERSION:
            raise ValueError('Unsupported catalog schema.')
        if type(data['release']) is not int or data['release'] < 1:
            raise ValueError('Invalid release number.')
        validate_publication(data['catalog'], data['reviews'])
        return data, CardDatabase.from_json(data['catalog'])
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise CatalogUpdateError(f'Invalid catalog publication: {error}') from error


class CatalogCache:
    def __init__(self, directory):
        self.path = Path(directory).resolve() / 'catalog.sqlite3'

    def load(self, baseline):
        """Fall back to the previous valid release or bundled baseline on corruption."""
        if not self.path.exists():
            return baseline
        try:
            with sqlite3.connect(f'{self.path.as_uri()}?mode=ro', uri=True) as connection:
                rows = connection.execute('SELECT body FROM releases ORDER BY release DESC').fetchall()
            for (raw,) in rows:
                try:
                    return decode_bundle(raw)[1]
                except CatalogUpdateError:
                    continue
        except sqlite3.Error:
            pass
        return baseline

    def install(self, raw):
        if len(raw) > MAX_BUNDLE_BYTES:
            raise CatalogUpdateError('Catalog exceeds the download limit.')
        publication, _ = decode_bundle(raw)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS releases '
                               '(release INTEGER PRIMARY KEY, body BLOB NOT NULL)')
            connection.execute('BEGIN IMMEDIATE')
            latest = connection.execute('SELECT MAX(release) FROM releases').fetchone()[0] or 0
            if publication['release'] <= latest:
                raise CatalogUpdateError('Catalog release must be newer than the installed release.')
            connection.execute('INSERT INTO releases VALUES (?, ?)', (publication['release'], raw))
            connection.execute('DELETE FROM releases WHERE release NOT IN '
                               '(SELECT release FROM releases ORDER BY release DESC LIMIT 2)')
        return publication['release']


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CatalogUpdateError('Catalog redirects are not permitted.')


def https_url(url):
    parsed = urlparse(url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.fragment):
        raise CatalogUpdateError('Catalog URLs must use HTTPS without credentials or fragments.')
    return parsed


def download(url, limit):
    https_url(url)
    opener = build_opener(NoRedirects())
    deadline = time.monotonic() + 30
    chunks = []
    size = 0
    with opener.open(url, timeout=10) as response:
        if response.status != 200:
            raise CatalogUpdateError('Catalog server did not return a complete response.')
        while True:
            chunk = response.read(min(65536, limit + 1 - size))
            if time.monotonic() > deadline:
                raise CatalogUpdateError('Catalog download exceeded its time budget.')
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise CatalogUpdateError('Catalog download exceeds the size limit.')
    return b''.join(chunks)


def update_catalog(manifest_url, cache, fetch=download):
    """Explicit update only. Failure never changes an installed catalog."""
    origin = https_url(manifest_url)
    try:
        manifest_raw = fetch(manifest_url, MAX_MANIFEST_BYTES)
        if len(manifest_raw) > MAX_MANIFEST_BYTES:
            raise ValueError('Manifest exceeds the size limit.')
        manifest = json.loads(manifest_raw)
        if manifest['schema_version'] != SCHEMA_VERSION:
            raise ValueError('Unsupported manifest schema.')
        size = manifest['size']
        if type(size) is not int or not 0 < size <= MAX_BUNDLE_BYTES:
            raise ValueError('Invalid bundle size.')
        target = urljoin(manifest_url, manifest['bundle'])
        parsed = https_url(target)
        if (parsed.hostname, parsed.port) != (origin.hostname, origin.port):
            raise ValueError('Bundle must use the configured catalog origin.')
        raw = fetch(target, size)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != manifest['sha256']:
            raise ValueError('Catalog size or checksum does not match the manifest.')
        publication, _ = decode_bundle(raw)
        if publication['release'] != manifest['release']:
            raise ValueError('Catalog release does not match the manifest.')
        return cache.install(raw)
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise CatalogUpdateError(f'Catalog update rejected: {error}') from error
