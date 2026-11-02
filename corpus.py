"""Small offline editorial evidence corpus, kept distinct from original source text."""
from dataclasses import asdict
import math
import re
from pathlib import Path
import json

from editorial import digest, entry_version
from identity import organism_key

FIELDS = ('description', 'habitat', 'environment_role', 'physical_dimensions', 'notes')
STOP = set('a an the what where when why how do does is are can could would should '
           'this that these those it its of in on at to for and or with about tell me '
           'please animal organism live lives living'.split())


def tokens(text):
    return {word.rstrip('s') for word in re.findall(r"[a-z]+", text.casefold())
            if word not in STOP and len(word) > 2}


def build_corpus(catalog):
    passages = []
    for entry in catalog['organisms']:
        if entry.get('content_kind') not in ('source_checked', 'reviewed'):
            continue
        for field in FIELDS:
            if not entry.get(field):
                continue
            sources = [source for source in entry['sources'] if field in source['supports']]
            text = entry[field]
            passages.append({'id': entry['organism_id'] + ':' + field,
                'organism_id': entry['organism_id'], 'field': field, 'text': text,
                'kind': 'editorial_summary', 'source_ids': [s['id'] for s in sources],
                'source_versions': {s['id']: digest(s) for s in sources},
                'content_sha256': digest(text), 'entry_sha256': entry_version(entry),
                'review_status': entry['content_kind'],
                'reuse_basis': 'Original VitaDex factual summary; not copied source prose. '
                               'Repository license applies to original wording.',
                'attribution': 'VitaDex; based on the linked source records, which retain their own terms.'})
    return {'version': 1, 'catalog_sha256': digest(catalog), 'passages': passages}


class Corpus:
    def __init__(self, catalog, data):
        expected = build_corpus(catalog)
        if data != expected:
            raise ValueError('Corpus is stale or modified; regenerate it from the source-bearing catalog.')
        self.catalog = {entry['organism_id']: entry for entry in catalog['organisms']}
        self.passages = data['passages']

    def references(self, passage):
        if passage not in self.passages:
            raise ValueError('Reference requested for a passage outside this corpus.')
        entry = self.catalog[passage['organism_id']]
        return [source for source in entry['sources'] if source['id'] in passage['source_ids']]

    @classmethod
    def bundled(cls):
        root = Path(__file__).parent / 'data'
        return cls(json.loads((root / 'database.json').read_text()),
                   json.loads((root / 'corpus.json').read_text()))

    def retrieve(self, species, question, limit=3, allow_source_checked=False):
        """Return evidence, never a generated answer. No implicit network access."""
        if not isinstance(question, str) or len(question) > 1000 or not 1 <= limit <= 5:
            raise ValueError('Use a question up to 1000 characters and a limit of 1–5.')
        if re.search(r'\b(dose|medicine|medication|poison|edible|toxic|bite|treat)\b', question, re.I):
            return []
        if re.search(r'\b(can|should|safe)\b.*\b(i|we|child)\b.*\b(eat|touch|feed|pet)\b', question, re.I):
            return []
        entry = self.catalog.get(species)
        if entry is None:
            return []
        query = tokens(question) - tokens(entry['name'] + ' ' + entry['scientific_name'])
        if not query:
            return []
        candidates = [p for p in self.passages if p['organism_id'] == species and
                      (p['review_status'] == 'reviewed' or allow_source_checked)]
        scored = []
        for passage in candidates:
            words = tokens(passage['text'])
            overlap = query & words
            if overlap:
                score = len(overlap) / math.sqrt(max(1, len(words)))
                scored.append((score, passage))
        return [passage for score, passage in sorted(scored, key=lambda x: (-x[0], x[1]['id']))[:limit]]


def snapshot_context(card, field):
    """Use the saved card's facts and citations, never a newer catalog's text under old citations."""
    entry = asdict(card.organism)
    if (entry['content_kind'] not in ('source_checked', 'reviewed')
            or field not in FIELDS or not entry.get(field)):
        return None
    return {'organism_id': organism_key(card.organism), 'field': field,
            'text': entry[field], 'kind': 'editorial_summary',
            'sources': [s for s in entry['sources'] if field in s['supports']]}
