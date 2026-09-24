import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_PATH = Path(__file__).parent / 'data' / 'database.json'


@dataclass
class CardBackground:
    id: str
    name: str
    style: str
    preview: str
    tags: List[str] = field(default_factory=list)
    description: str = ''


@dataclass
class OrganismArt:
    organism_name: str
    prompt: str
    assets: List[str] = field(default_factory=list)


@dataclass
class OrganismEntry:
    name: str
    type: str
    description: str
    habitat: str
    environment_role: str
    rarity: str
    move_set: List[str] = field(default_factory=list)
    related_forms: List[str] = field(default_factory=list)
    lifecycle_stage: str = ''
    group: str = ''
    notes: str = ''
    physical_dimensions: str = ''
    habitat_type: str = ''


@dataclass
class Card:
    organism: OrganismEntry
    background: CardBackground
    art_asset: str
    selected_moves: List[str]
    selected_details: Dict[str, str]

    @property
    def card_art(self) -> str:
        return self.art_asset

    @property
    def title(self) -> str:
        return self.organism.name


@dataclass
class CardDatabase:
    backgrounds: List[CardBackground]
    organisms: Dict[str, OrganismEntry]
    art_sets: Dict[str, OrganismArt]

    @classmethod
    def from_json(cls, data: dict) -> 'CardDatabase':
        cls.validate_data(data)
        backgrounds = [CardBackground(**background) for background in data.get('background_templates', [])]
        organisms = {
            entry['name']: OrganismEntry(**entry)
            for entry in data.get('organisms', [])
        }
        art_sets = {
            art['organism_name']: OrganismArt(**art)
            for art in data.get('art_assets', [])
        }
        return cls(backgrounds=backgrounds, organisms=organisms, art_sets=art_sets)

    @staticmethod
    def validate_data(data: Any) -> None:
        """Validate the catalog invariants required to build a collectible card.

        JSON Schema validation remains useful for externally published catalog
        files, but these checks keep the app from starting with a catalog that
        cannot produce a card even when it is loaded directly from disk.
        """
        if not isinstance(data, dict):
            raise ValueError('Card database must be a JSON object.')

        required_sections = ('background_templates', 'organisms', 'art_assets')
        for section in required_sections:
            if not isinstance(data.get(section), list):
                raise ValueError(f'Card database section {section!r} must be a list.')

        backgrounds = data['background_templates']
        organisms = data['organisms']
        art_assets = data['art_assets']
        if not backgrounds:
            raise ValueError('Card database must contain at least one background template.')
        if not organisms:
            raise ValueError('Card database must contain at least one organism.')

        background_ids = set()
        for background in backgrounds:
            if not isinstance(background, dict):
                raise ValueError('Every background template must be an object.')
            missing = {'id', 'name', 'style', 'preview'} - background.keys()
            if missing:
                raise ValueError(f'Background template is missing fields: {sorted(missing)}.')
            if not background['id']:
                raise ValueError('Every background template must have a non-empty id.')
            if background['id'] in background_ids:
                raise ValueError(f'Duplicate background id: {background["id"]!r}.')
            background_ids.add(background['id'])

        organism_names = set()
        for organism in organisms:
            if not isinstance(organism, dict):
                raise ValueError('Every organism must be an object.')
            missing = {
                'name', 'type', 'description', 'habitat', 'environment_role', 'rarity'
            } - organism.keys()
            if missing:
                raise ValueError(f'Organism is missing fields: {sorted(missing)}.')
            if not organism['name']:
                raise ValueError('Every organism must have a non-empty name.')
            if organism['name'] in organism_names:
                raise ValueError(f'Duplicate organism name: {organism["name"]!r}.')
            organism_names.add(organism['name'])

        for art in art_assets:
            if not isinstance(art, dict):
                raise ValueError('Every art asset entry must be an object.')
            missing = {'organism_name', 'prompt', 'assets'} - art.keys()
            if missing:
                raise ValueError(f'Art asset entry is missing fields: {sorted(missing)}.')
            if not art['organism_name']:
                raise ValueError('Every art asset entry must name an organism.')
            if art['organism_name'] not in organism_names:
                raise ValueError(
                    f'Art asset references unknown organism: {art["organism_name"]!r}.'
                )

    @classmethod
    def load_default(cls, path: Optional[Path] = None) -> 'CardDatabase':
        path = path or DATA_PATH
        if path.exists():
            with path.open('r', encoding='utf-8') as handle:
                data = json.load(handle)
            return cls.from_json(data)
        return cls.from_json(DEFAULT_DATABASE)

    def get_organism(self, name: str) -> Optional[OrganismEntry]:
        return self.organisms.get(name)

    def get_random_organism(self) -> OrganismEntry:
        return random.choice(list(self.organisms.values()))

    def get_art_for(self, organism: OrganismEntry) -> Optional[OrganismArt]:
        return self.art_sets.get(organism.name)

    def select_background_for(self, organism: OrganismEntry) -> CardBackground:
        preferences = {organism.type.lower(), organism.habitat_type.lower(), organism.group.lower()}
        matching = [background for background in self.backgrounds if any(tag.lower() in preferences for tag in background.tags)]
        if matching:
            return random.choice(matching)
        return random.choice(self.backgrounds)

    def select_art_asset(self, organism: OrganismEntry) -> str:
        art_set = self.get_art_for(organism)
        if art_set and art_set.assets:
            return random.choice(art_set.assets)
        return organism.name[:1]

    def select_moves(self, organism: OrganismEntry, count: int = 3) -> List[str]:
        if not organism.move_set:
            return []
        return random.sample(organism.move_set, min(count, len(organism.move_set)))

    def build_card(self, organism: OrganismEntry) -> Card:
        background = self.select_background_for(organism)
        art_asset = self.select_art_asset(organism)
        selected_moves = self.select_moves(organism)
        selected_details = {
            'Habitat': organism.habitat_type or organism.habitat,
            'Size': organism.physical_dimensions or 'Unknown',
            'Role': organism.environment_role,
        }
        return Card(
            organism=organism,
            background=background,
            art_asset=art_asset,
            selected_moves=selected_moves,
            selected_details=selected_details,
        )


DEFAULT_DATABASE = {
    'background_templates': [
        {
            'id': 'forest_emerald',
            'name': 'Forest Glow',
            'style': 'emerald',
            'preview': 'Forest',
            'tags': ['Bug', 'Plant', 'Forest'],
            'description': 'A soft green card background with forest leaf textures and glow accents.',
        },
        {
            'id': 'stream_splash',
            'name': 'Stream Splash',
            'style': 'blue',
            'preview': 'Stream',
            'tags': ['Fish', 'Water', 'Freshwater'],
            'description': 'A cool blue water card backdrop with subtle current lines and splash details.',
        },
        {
            'id': 'sunshine_halo',
            'name': 'Sunshine Halo',
            'style': 'gold',
            'preview': 'Sun',
            'tags': ['Plant', 'Meadow', 'Sun'],
            'description': 'A bright golden card frame with warm sun flares and floral highlights.',
        },
    ],
    'organisms': [
        {
            'name': 'Glowleaf Beetle',
            'type': 'Bug',
            'move_set': ['Leaf Glow', 'Sticky Climb', 'Camouflage Drift', 'Moss Spark'],
            'description': 'A small forest crawler that lights up mossy paths and helps break down fallen leaves.',
            'habitat': 'Mossy forest floors, damp clearings, and shaded wetlands',
            'habitat_type': 'Forest',
            'environment_role': 'Pollinator and decomposer contributing to forest health',
            'physical_dimensions': '3 cm long',
            'rarity': 'Common',
            'related_forms': ['Glowleaf Larva', 'Glowleaf Pupa'],
            'lifecycle_stage': 'Adult',
            'group': 'Glowleaf Beetle Family',
            'notes': 'Often found near decaying logs in low light areas.',
        },
        {
            'name': 'Streamfin Dart',
            'type': 'Fish',
            'move_set': ['Ripple Dash', 'Bubble Flicker', 'Current Veil'],
            'description': 'A fast-moving water creature that darts through stream pools and helps keep currents clean.',
            'habitat': 'Freshwater streams, ponds, and slow rivers',
            'habitat_type': 'Freshwater',
            'environment_role': 'Water cleaner and algae balancer for healthy waterways',
            'physical_dimensions': '15 cm long',
            'rarity': 'Uncommon',
            'related_forms': ['Streamfin Fry'],
            'lifecycle_stage': 'Adult',
            'group': 'Streamfin Species',
            'notes': 'Best spotted near submerged plants and gentle currents.',
        },
        {
            'name': 'Sunflare Sprout',
            'type': 'Plant',
            'move_set': ['Solar Reach', 'Petal Shield', 'Seed Drift'],
            'description': 'A bright, cheerful plant that opens in sunlight and provides food and shelter to small wildlife.',
            'habitat': 'Sunny meadows, hillsides, and garden edges',
            'habitat_type': 'Meadow',
            'environment_role': 'Food source and nesting cover for insects and small animals',
            'physical_dimensions': '50 cm tall',
            'rarity': 'Rare',
            'related_forms': ['Sunflare Seedling'],
            'lifecycle_stage': 'Adult',
            'group': 'Sunflare Plants',
            'notes': 'The most eye-catching cards show it glowing in golden hour light.',
        },
    ],
    'art_assets': [
        {
            'organism_name': 'Glowleaf Beetle',
            'prompt': 'A tiny glowing beetle perched on a mossy leaf, soft bioluminescent light, collectible card illustration',
            'assets': ['Glowleaf Art 1', 'Glowleaf Art 2', 'Glowleaf Art 3'],
        },
        {
            'organism_name': 'Streamfin Dart',
            'prompt': 'A swift silver fish in a clear stream, shimmering water reflections, collectible card art',
            'assets': ['Streamfin Art 1', 'Streamfin Art 2', 'Streamfin Art 3'],
        },
        {
            'organism_name': 'Sunflare Sprout',
            'prompt': 'A bright sunflower-like sprout glowing in golden hour light, cheerful collectible card art',
            'assets': ['Sunflare Art 1', 'Sunflare Art 2', 'Sunflare Art 3'],
        },
    ],
}


CARD_DB = CardDatabase.load_default()
