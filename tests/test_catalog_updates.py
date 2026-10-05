import hashlib
import json
import sqlite3

import pytest

from catalog_updates import CatalogCache, CatalogUpdateError, update_catalog
from database import NATURE_DB
from scripts.publish_catalog import publish
from test_catalog_review import publication


def bundle(release=1):
    catalog, reviews = publication()
    return json.dumps(dict(schema_version=1, release=release, catalog=catalog, reviews=reviews)).encode()


def fetcher(raw, **overrides):
    manifest = dict(schema_version=1, release=1, bundle='catalog.json', size=len(raw),
                    sha256=hashlib.sha256(raw).hexdigest())
    manifest.update(overrides)
    def fetch(url, limit):
        return json.dumps(manifest).encode() if url.endswith('manifest.json') else raw
    return fetch


def test_cache_needs_no_network_and_recovers_previous_snapshot(tmp_path):
    cache = CatalogCache(tmp_path)
    assert cache.load(NATURE_DB) is NATURE_DB
    cache.install(bundle(1))
    cache.install(bundle(2))
    with sqlite3.connect(cache.path) as connection:
        connection.execute('UPDATE releases SET body=? WHERE release=2', (b'broken',))
    assert cache.load(NATURE_DB).organisms['Ladybird beetle'].review_status == 'reviewed'
    with pytest.raises(CatalogUpdateError, match='newer'):
        cache.install(bundle(1))


def test_invalid_download_leaves_current_catalog_untouched(tmp_path):
    cache = CatalogCache(tmp_path)
    cache.install(bundle(1))
    before = cache.path.read_bytes()
    for overrides in (dict(sha256='bad'), dict(size=1), dict(release=50),
                      dict(bundle='https://another.example/catalog.json'), dict(schema_version=99)):
        with pytest.raises(CatalogUpdateError):
            update_catalog('https://example.org/manifest.json', cache, fetcher(bundle(2), **overrides))
        assert cache.path.read_bytes() == before


def test_successful_update_and_retention(tmp_path):
    cache = CatalogCache(tmp_path)
    assert update_catalog('https://example.org/manifest.json', cache, fetcher(bundle())) == 1
    cache.install(bundle(2))
    cache.install(bundle(3))
    with sqlite3.connect(cache.path) as connection:
        assert connection.execute('SELECT release FROM releases ORDER BY release').fetchall() == [(2,), (3,)]


def test_publication_round_trip_and_immutable_output(tmp_path):
    catalog, reviews = publication()
    manifest_path = publish(catalog, reviews, 1, tmp_path / 'published')
    manifest = json.loads(manifest_path.read_text())
    raw = (manifest_path.parent / manifest['bundle']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest['sha256']
    with pytest.raises(FileExistsError):
        publish(catalog, reviews, 1, tmp_path / 'published')
    assert update_catalog('https://example.org/manifest.json', CatalogCache(tmp_path / 'cache'),
                          lambda url, limit: manifest_path.read_bytes() if url.endswith('manifest.json') else raw) == 1


def test_drafts_and_insecure_urls_rejected(tmp_path):
    catalog, reviews = publication()
    catalog['organisms'][0]['review_status'] = 'draft'
    with pytest.raises(CatalogUpdateError):
        publish(catalog, reviews, 1, tmp_path)
    with pytest.raises(CatalogUpdateError, match='HTTPS'):
        update_catalog('http://example.org/manifest.json', CatalogCache(tmp_path), lambda *_: b'')


def test_ambiguous_model_mapping_cannot_replace_working_catalog(tmp_path):
    cache = CatalogCache(tmp_path)
    cache.install(bundle())
    data = json.loads(bundle(2))
    data['catalog']['organisms'][1]['model_labels'] = data['catalog']['organisms'][0]['model_labels']
    with pytest.raises(CatalogUpdateError, match='ambiguous'):
        cache.install(json.dumps(data).encode())


def test_download_failure_does_not_create_a_cache(tmp_path):
    cache = CatalogCache(tmp_path)
    def failed(*_):
        raise OSError('network disconnected')
    with pytest.raises(CatalogUpdateError, match='network disconnected'):
        update_catalog('https://example.org/manifest.json', cache, failed)
    assert not cache.path.exists()
