import copy
import json
from pathlib import Path

import pytest

from catalog_review import FACT_FIELDS, validate_publication


def publication():
    data = json.loads(Path('data/nature_catalog.json').read_text())
    reviews = {}
    for entry in data['organisms']:
        entry['revision'] = 1
        entry['review_status'] = 'reviewed'
        entry['fact_sources'] = {field: entry['references'] for field in FACT_FIELDS if entry.get(field)}
        reviews[entry['id']] = dict(revision=1, author='test-author', reviewer='test-reviewer',
                                   decision='approved', date='2026-01-01')
    return data, reviews


def test_bundled_drafts_cannot_be_published():
    data = json.loads(Path('data/nature_catalog.json').read_text())
    with pytest.raises(ValueError, match='reviewed'):
        validate_publication(data, {})


def test_recorded_review_and_sources_are_required_for_each_revision():
    data, reviews = publication()
    validate_publication(data, reviews)
    changed = copy.deepcopy(data)
    changed['organisms'][0]['revision'] = 2
    with pytest.raises(ValueError, match='approval'):
        validate_publication(changed, reviews)
    changed = copy.deepcopy(data)
    changed['organisms'][0]['fact_sources'].pop('description')
    with pytest.raises(ValueError, match='description'):
        validate_publication(changed, reviews)


def test_self_approval_is_rejected():
    data, reviews = publication()
    review = next(iter(reviews.values()))
    review['reviewer'] = review['author']
    with pytest.raises(ValueError, match='approval'):
        validate_publication(data, reviews)
