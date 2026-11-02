"""Stable bundled taxon identities; aliases preserve discovery history on renames."""
ALIASES = {
    'canis lupus familiaris': 'dog', 'canis familiaris': 'dog',
    'felis catus': 'cat', 'acer rubrum': 'red-maple',
    'poa pratensis': 'kentucky-bluegrass', 'turdus migratorius': 'american-robin',
}
LEGACY_NAMES = {'dog': 'dog', 'cat': 'cat', 'red maple': 'red-maple',
                'kentucky bluegrass': 'kentucky-bluegrass', 'american robin': 'american-robin'}


def organism_key(organism):
    if organism.content_kind == 'fictional':
        return organism.organism_id or 'fictional:' + organism.name.strip().casefold()
    name = organism.scientific_name.strip().casefold()
    known = ALIASES.get(name) or (LEGACY_NAMES.get(organism.name.strip().casefold()) if not name else None)
    return 'taxon:' + known if known else (organism.organism_id or 'species:' + (name or organism.name.strip().casefold()))
