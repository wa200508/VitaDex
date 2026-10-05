import json
from pathlib import Path

import pytest

from catalog_review import FACT_FIELDS, validate_publication
from database import CardDatabase


def test_review_draft_is_loadable_cited_and_never_publishable_without_approval():
    data = json.loads(Path('docs/drafts/catalog-review-01.json').read_text())
    catalog = CardDatabase.from_json(data)
    assert len(catalog.organisms) == 4
    assert {entry.type for entry in catalog.organisms.values()} == {'Mammal', 'Plant', 'Fungus', 'Bacterium'}
    for entry in catalog.organisms.values():
        assert entry.review_status == 'draft'
        assert not entry.model_labels
        for field in FACT_FIELDS:
            if getattr(entry, field):
                assert entry.fact_sources[field]
                assert set(entry.fact_sources[field]) <= set(entry.references)
    with pytest.raises(ValueError, match='reviewed'):
        validate_publication(data, {})
