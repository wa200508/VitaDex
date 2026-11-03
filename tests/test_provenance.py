"""Synthetic references test the contract; they are not published card citations."""
from copy import deepcopy
from dataclasses import asdict, replace

import pytest

from database import DEMO_DB as CARD_DB, OrganismEntry
from journal import JournalRepository
from provenance import FACT_FIELDS, validate_provenance


def reviewed_entry():
    data = asdict(next(iter(CARD_DB.organisms.values())))
    data.update(content_kind='reviewed', scientific_name='Test organism',
                reviewed_by='Test reviewer', reviewed_on='2026-11-01', sources=[{
                    'id': 'test-reference', 'title': 'Synthetic reference',
                    'publisher': 'Test publisher', 'url': 'https://example.org/test',
                    'revision_url': 'https://example.org/test?v=1',
                    'accessed_on': '2026-11-01', 'license': 'Synthetic test data',
                    'attribution': 'Test fixture only', 'supports': list(FACT_FIELDS),
                }])
    return data


def test_reviewed_card_preserves_source_snapshot_across_restart(tmp_path):
    organism = OrganismEntry(**reviewed_entry())
    card = CARD_DB.build_card(organism)
    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    repository.save_cards([card])
    organism.sources[0]['title'] = 'Changed after saving'
    loaded = repository.load_cards()[0]
    assert loaded.organism.sources[0]['title'] == 'Synthetic reference'
    assert loaded.organism.reviewed_by == 'Test reviewer'


def test_unreviewed_content_cannot_generate_new_card():
    organism = replace(next(iter(CARD_DB.organisms.values())), content_kind='unreviewed')
    with pytest.raises(ValueError, match='reviewed, cited'):
        CARD_DB.build_card(organism)


def test_old_snapshot_loads_as_unreviewed_without_fabricating_sources():
    card = CARD_DB.build_card(next(iter(CARD_DB.organisms.values())))
    snapshot = JournalRepository._card_to_dict(card)
    for field in ('content_kind', 'scientific_name', 'sources', 'reviewed_by', 'reviewed_on'):
        snapshot['organism'].pop(field)
    loaded = JournalRepository._card_from_dict(snapshot)
    assert loaded.organism.content_kind == 'unreviewed'
    assert loaded.organism.sources == []


@pytest.mark.parametrize('mutation', [
    lambda data: data.update(sources=[]),
    lambda data: data.update(reviewed_by=''),
    lambda data: data.update(reviewed_on='not-a-date'),
    lambda data: data.update(scientific_name=''),
    lambda data: data['sources'][0].update(supports=['description']),
    lambda data: data['sources'][0].update(url='javascript:alert(1)'),
    lambda data: data['sources'][0].update(url='https://user:secret@example.org'),
    lambda data: data['sources'][0].update(revision_url=123),
    lambda data: data['sources'][0].update(accessed_on='bad date'),
    lambda data: data['sources'][0].update(license=''),
    lambda data: data['sources'].append(deepcopy(data['sources'][0])),
])
def test_invalid_or_incomplete_provenance_is_rejected(mutation):
    data = reviewed_entry()
    mutation(data)
    with pytest.raises(ValueError):
        validate_provenance(data)


def test_demo_catalog_is_explicitly_fictional():
    assert all(item.content_kind == 'fictional' and not item.sources
               for item in CARD_DB.organisms.values())


def test_source_checked_requires_citations_without_claiming_human_review():
    data = reviewed_entry()
    data['content_kind'] = 'source_checked'
    validate_provenance(data)
    data['sources'][0]['supports'] = ['description']
    with pytest.raises(ValueError, match='uncited facts'):
        validate_provenance(data)


@pytest.mark.parametrize('evidence', [None, {}, {'location': 'Description', 'excerpt': 'test', 'sha256': 'wrong'}])
def test_malformed_or_modified_evidence_is_rejected(evidence):
    data = reviewed_entry()
    data['sources'][0]['evidence'] = evidence
    with pytest.raises(ValueError, match='evidence'):
        validate_provenance(data)
