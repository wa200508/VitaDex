"""Version-bound editorial review records; no automatic human approval."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from provenance import FACT_FIELDS


CHECKS = ('facts_supported', 'scientific_names', 'child_readability', 'reuse_and_attribution')


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':')).encode()).hexdigest()


def entry_version(entry):
    return digest({key: value for key, value in entry.items()
                   if key not in ('content_kind', 'reviewed_by', 'reviewed_on')})


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         delete=False) as output:
            name = output.name
            json.dump(data, output, indent=2, ensure_ascii=False)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()


def review_packet(catalog):
    return {'version': 1, 'entries': [
        {'organism_id': entry['organism_id'], 'name': entry['name'],
         'entry_sha256': entry_version(entry), 'decision': 'pending',
         'reviewer_kind': '', 'reviewer': '', 'reviewed_on': '',
         'checks': dict.fromkeys(CHECKS, False), 'notes': '',
         'claims': {key: {'text': entry[key], 'sources': [
             source['id'] for source in entry['sources'] if key in source['supports']]}
             for key in FACT_FIELDS if entry.get(key)},
         'references': deepcopy(entry['sources'])}
        for entry in catalog['organisms'] if entry.get('content_kind') != 'fictional']}


def apply_review(catalog, packet):
    if packet.get('version') != 1 or not isinstance(packet.get('entries'), list):
        raise ValueError('Unsupported review packet.')
    updated = deepcopy(catalog)
    by_id = {entry['organism_id']: entry for entry in updated['organisms']}
    seen = set()
    for review in packet['entries']:
        key = review['organism_id']
        if key in seen or key not in by_id:
            raise ValueError('Duplicate or unknown organism in review.')
        seen.add(key)
        entry = by_id[key]
        if review['entry_sha256'] != entry_version(entry):
            raise ValueError(f'Stale review for {key}; facts or sources changed.')
        expected = next(x for x in review_packet(catalog)['entries'] if x['organism_id'] == key)
        if review.get('claims') != expected['claims'] or review.get('references') != expected['references']:
            raise ValueError('Review packet claims or references were altered; regenerate the packet.')
        decision = review.get('decision')
        if decision == 'pending':
            continue
        if decision not in ('approved', 'changes_requested'):
            raise ValueError('Unknown review decision.')
        if review.get('reviewer_kind') != 'human' or not review.get('reviewer', '').strip():
            raise ValueError('A named human reviewer must declare this decision.')
        reviewed = date.fromisoformat(review['reviewed_on'])
        if reviewed > date.today():
            raise ValueError('Review dates cannot be in the future.')
        if decision == 'changes_requested':
            entry['content_kind'] = 'unreviewed'
        else:
            if any(review.get('checks', {}).get(key) is not True for key in CHECKS):
                raise ValueError('All editorial checks must be explicitly completed.')
            entry['content_kind'] = 'reviewed'
        entry['reviewed_by'], entry['reviewed_on'] = review['reviewer'], review['reviewed_on']
    return updated


def changed_fields(saved, current):
    return [key for key in sorted(set(saved) | set(current)) if saved.get(key) != current.get(key)]
