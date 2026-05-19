from dataclasses import dataclass, field
from typing import List


@dataclass
class OrganismEntry:
    name: str
    type: str
    move_set: List[str]
    description: str
    habitat: str
    environment_role: str
    art: str
    rarity: str
    image_assets: List[str]
    related_forms: List[str] = field(default_factory=list)
    lifecycle_stage: str = ''
    group: str = ''
    notes: str = ''


DATABASE = [
    OrganismEntry(
        name='Glowleaf Beetle',
        type='Bug',
        move_set=['Leaf Glow', 'Sticky Climb', 'Camouflage Drift'],
        description='A small forest crawler that lights up mossy paths and helps break down fallen leaves.',
        habitat='Mossy forest floors, damp clearings, and shaded wetlands',
        environment_role='Pollinator and decomposer contributing to forest health',
        art='🪲💚',
        rarity='Common',
        image_assets=['🪲💚', '🍃✨', '🌿🪲'],
        group='Glowleaf Beetle Family',
        lifecycle_stage='Adult',
        related_forms=['Glowleaf Larva', 'Glowleaf Pupa'],
        notes='Often found near decaying logs in low light areas.',
    ),
    OrganismEntry(
        name='Streamfin Dart',
        type='Fish',
        move_set=['Ripple Dash', 'Bubble Flicker', 'Current Veil'],
        description='A fast-moving water creature that darts through stream pools and helps keep currents clean.',
        habitat='Freshwater streams, ponds, and slow rivers',
        environment_role='Water cleaner and algae balancer for healthy waterways',
        art='🐟💧',
        rarity='Uncommon',
        image_assets=['🐟💧', '💦🌊', '🌿🐟'],
        group='Streamfin Species',
        lifecycle_stage='Adult',
        related_forms=['Streamfin Fry'],
        notes='Best spotted near submerged plants and gentle currents.',
    ),
    OrganismEntry(
        name='Sunflare Sprout',
        type='Plant',
        move_set=['Solar Reach', 'Petal Shield', 'Seed Drift'],
        description='A bright, cheerful plant that opens in sunlight and provides food and shelter to small wildlife.',
        habitat='Sunny meadows, hillsides, and garden edges',
        environment_role='Food source and nesting cover for insects and small animals',
        art='🌼☀️',
        rarity='Rare',
        image_assets=['🌼☀️', '🌻✨', '🌿🌞'],
        group='Sunflare Plants',
        lifecycle_stage='Adult',
        related_forms=['Sunflare Seedling'],
        notes='The most eye-catching cards show it glowing in golden hour light.',
    ),
    OrganismEntry(
        name='Glowleaf Larva',
        type='Bug',
        move_set=['Moss Munch', 'Shelter Spin'],
        description='The juvenile form of Glowleaf Beetle, found in damp leaf litter where it feeds and grows safely.',
        habitat='Leaf litter and rotten logs in shaded forests',
        environment_role='Early-stage decomposer and nutrient recycler',
        art='🐛✨',
        rarity='Common',
        image_assets=['🐛✨', '🍂🐛'],
        group='Glowleaf Beetle Family',
        lifecycle_stage='Larva',
        related_forms=['Glowleaf Beetle', 'Glowleaf Pupa'],
    ),
    OrganismEntry(
        name='Streamfin Fry',
        type='Fish',
        move_set=['Mini Splash', 'Current Trace'],
        description='A young streamfin that stays near the shallows while it grows stronger and learns to navigate currents.',
        habitat='Shallow stream edges and quiet backwaters',
        environment_role='Juvenile cleaner helping maintain healthy stream surfaces',
        art='🐟🫧',
        rarity='Common',
        image_assets=['🐟🫧', '🌊🐟'],
        group='Streamfin Species',
        lifecycle_stage='Juvenile',
        related_forms=['Streamfin Dart'],
    ),
    OrganismEntry(
        name='Sunflare Seedling',
        type='Plant',
        move_set=['Tiny Reach', 'Sun Sway'],
        description='A young Sunflare plant that begins its life sheltered in tall grass before opening to the sun.',
        habitat='Seedling patches in sunny meadows',
        environment_role='Early growth stage that prepares the ground for adult plant communities',
        art='🌱☀️',
        rarity='Uncommon',
        image_assets=['🌱☀️', '🌿🌻'],
        group='Sunflare Plants',
        lifecycle_stage='Seedling',
        related_forms=['Sunflare Sprout'],
    ),
]
