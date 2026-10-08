import json

import pytest

from catalog_updates import CatalogCache, CatalogUpdateError, update_catalog
from scripts.prepare_catalog_host import prepare
from test_catalog_review import publication


def inputs(source, release=1):
    source.mkdir(exist_ok=True)
    catalog, reviews = publication()
    for name, value in [('catalog.json', catalog), ('reviews.json', reviews),
                        ('release.json', {'release': release})]:
        (source / name).write_text(json.dumps(value))


def test_bootstrap_reports_pending_without_publishing_fake_facts(tmp_path):
    manifest = prepare(tmp_path / 'absent', tmp_path / 'host')
    assert json.loads(manifest.read_text()) == {'schema_version': 1, 'status': 'awaiting_review'}
    cache = CatalogCache(tmp_path / 'cache')
    with pytest.raises(CatalogUpdateError, match='No reviewed catalog'):
        update_catalog('https://example.org/manifest.json', cache, lambda *_: manifest.read_bytes())
    assert not cache.path.exists()
    assert not list(manifest.parent.glob('catalog-*.json'))


def test_publisher_validates_and_retry_cannot_overwrite_same_release(tmp_path):
    source, host = tmp_path / 'source', tmp_path / 'host'
    inputs(source)
    manifest = prepare(source, host)
    before = manifest.read_bytes()
    assert prepare(source, host).read_bytes() == before
    catalog = json.loads((source / 'catalog.json').read_text())
    catalog['organisms'][0]['name'] = 'Changed'
    (source / 'catalog.json').write_text(json.dumps(catalog))
    with pytest.raises(ValueError, match='different content'):
        prepare(source, host)
    assert manifest.read_bytes() == before
    inputs(source, 2)
    prepare(source, host)
    assert len(list(host.glob('catalog-*.json'))) == 2
    inputs(source, 1)
    with pytest.raises(ValueError, match='newer'):
        prepare(source, host)


def test_missing_review_and_drafts_cannot_change_public_files(tmp_path):
    source, host = tmp_path / 'source', tmp_path / 'host'
    prepare(source, host)
    before = (host / 'manifest.json').read_bytes()
    inputs(source)
    (source / 'reviews.json').unlink()
    with pytest.raises(ValueError, match='all be present'):
        prepare(source, host)
    inputs(source)
    catalog = json.loads((source / 'catalog.json').read_text())
    catalog['organisms'][0]['review_status'] = 'draft'
    (source / 'catalog.json').write_text(json.dumps(catalog))
    with pytest.raises(CatalogUpdateError):
        prepare(source, host)
    assert (host / 'manifest.json').read_bytes() == before


def test_removing_inputs_does_not_withdraw_publication(tmp_path):
    source, host = tmp_path / 'source', tmp_path / 'host'
    inputs(source)
    manifest = prepare(source, host)
    before = manifest.read_bytes()
    for path in source.iterdir():
        path.unlink()
    assert prepare(source, host).read_bytes() == before


def test_empty_catalog_cannot_be_published_as_reviewed(tmp_path):
    source, host = tmp_path / 'source', tmp_path / 'host'
    inputs(source)
    catalog = json.loads((source / 'catalog.json').read_text())
    catalog['organisms'] = []
    (source / 'catalog.json').write_text(json.dumps(catalog))
    with pytest.raises(CatalogUpdateError, match='at least one organism'):
        prepare(source, host)
    assert not host.exists()
