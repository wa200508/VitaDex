import json
from pathlib import Path

import pytest

from database import CARD_DB, CardDatabase


REPOSITORY_ROOT = Path(__file__).parents[1]


def test_checked_in_catalog_loads_and_can_build_cards():
    assert len(CARD_DB.backgrounds) == 3
    assert set(CARD_DB.organisms) == {'Dog', 'Cat', 'Red Maple', 'Kentucky Bluegrass', 'American Robin'}

    for organism in CARD_DB.organisms.values():
        card = CARD_DB.build_card(organism)

        assert card.title == organism.name
        assert card.background in CARD_DB.backgrounds
        assert card.selected_details['Habitat']
        assert len(card.selected_moves) <= 3


def test_catalog_conforms_to_its_json_schema():
    jsonschema = pytest.importorskip('jsonschema')
    schema = json.loads((REPOSITORY_ROOT / 'card_database_schema.json').read_text())
    data = json.loads((REPOSITORY_ROOT / 'data' / 'database.json').read_text())

    jsonschema.validate(instance=data, schema=schema)


@pytest.mark.parametrize(
    ('data', 'message'),
    [
        ({'background_templates': [], 'organisms': [], 'art_assets': []}, 'background'),
        (
            {
                'background_templates': [
                    {'id': 'one', 'name': 'One', 'style': 'blue', 'preview': 'One'}
                ],
                'organisms': [
                    {
                        'name': 'Oak',
                        'type': 'Plant',
                        'description': 'A tree.',
                        'habitat': 'Forest',
                        'environment_role': 'Shelter',
                        'rarity': 'Common',
                    }
                ],
                'art_assets': [
                    {'organism_name': 'Unknown', 'prompt': 'art', 'assets': ['asset']}
                ],
            },
            'unknown organism',
        ),
    ],
)
def test_invalid_catalogs_are_rejected(data, message):
    with pytest.raises(ValueError, match=message):
        CardDatabase.from_json(data)


def test_ohio_starter_has_cited_short_introductions_and_no_fantasy_moves():
    from discovery import introduction
    from provenance import validate_provenance
    from dataclasses import asdict

    for organism in CARD_DB.organisms.values():
        assert organism.content_kind == 'source_checked'
        assert 'human review pending' in organism.reviewed_by
        assert 15 <= len(organism.description.split()) <= 45
        assert not organism.move_set
        assert organism.sources
        assert all(source.get('evidence') for source in organism.sources)
        validate_provenance(asdict(organism))
        narration = introduction(CARD_DB.build_card(organism))
        assert narration == f'{organism.name}. {organism.description}'
        assert 'Fictional' not in narration


def test_missing_catalog_does_not_silently_substitute_fiction(tmp_path):
    with pytest.raises(FileNotFoundError, match='Catalog not found'):
        CardDatabase.load_default(tmp_path / 'missing.json')
