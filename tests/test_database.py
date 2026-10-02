import json
from pathlib import Path

import pytest

from database import CARD_DB, CardDatabase


REPOSITORY_ROOT = Path(__file__).parents[1]


def test_checked_in_catalog_loads_and_can_build_cards():
    assert len(CARD_DB.backgrounds) == 3
    assert len(CARD_DB.organisms) == 3

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


def test_real_catalog_conforms_to_schema_and_has_distinct_model_labels():
    from database import NATURE_DB
    jsonschema = pytest.importorskip('jsonschema')
    schema = json.loads((REPOSITORY_ROOT / 'card_database_schema.json').read_text())
    data = json.loads((REPOSITORY_ROOT / 'data' / 'nature_catalog.json').read_text())
    jsonschema.validate(instance=data, schema=schema)
    identifiers = set()
    labels = set()
    for organism in NATURE_DB.organisms.values():
        assert not organism.is_demo
        assert organism.id and organism.id not in identifiers
        assert organism.scientific_name and organism.safety_message and organism.references
        identifiers.add(organism.id)
        for label in organism.model_labels:
            assert label not in labels
            labels.add(label)
        assert NATURE_DB.build_card(organism).title == organism.name
