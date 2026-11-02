"""Validate claim-level references without treating a URL as proof of review."""
from datetime import date
from hashlib import sha256
from urllib.parse import urlsplit

FACT_FIELDS = ('scientific_name', 'name', 'type', 'description', 'habitat', 'habitat_type', 'environment_role',
               'physical_dimensions', 'related_forms', 'lifecycle_stage', 'group', 'notes')
CONTENT_KINDS = ('fictional', 'unreviewed', 'source_checked', 'reviewed')


def validate_provenance(entry: dict) -> None:
    kind = entry.get('content_kind', 'unreviewed')
    if kind not in CONTENT_KINDS:
        raise ValueError('Unknown content_kind.')
    for field in ('scientific_name', 'reviewed_by', 'reviewed_on'):
        if not isinstance(entry.get(field, ''), str):
            raise ValueError(f'{field} must be text.')
    sources = entry.get('sources', [])
    if not isinstance(sources, list):
        raise ValueError('sources must be a list.')
    ids = set()
    covered = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError('Each source must be an object.')
        for field in ('id', 'title', 'publisher', 'url', 'accessed_on', 'license', 'attribution'):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f'Source {field} must be non-empty text.')
        if source['id'] in ids:
            raise ValueError('Source ids must be unique within an organism.')
        ids.add(source['id'])
        for field in ('url', 'revision_url'):
            if field == 'revision_url' and not source.get(field):
                continue
            if not isinstance(source[field], str):
                raise ValueError('Source links must be text.')
            url = urlsplit(source[field])
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                raise ValueError('Source links must use HTTPS without embedded credentials.')
        date.fromisoformat(source['accessed_on'])
        if 'evidence' in source:
            evidence = source['evidence']
            if not isinstance(evidence, dict) or any(
                not isinstance(evidence.get(field), str) or not evidence[field].strip()
                for field in ('location', 'excerpt', 'sha256')
            ):
                raise ValueError('Source evidence requires location, excerpt, and sha256 text.')
            if sha256(evidence['excerpt'].encode()).hexdigest() != evidence['sha256']:
                raise ValueError('Source evidence checksum does not match its excerpt.')
        claims = source.get('supports')
        if not isinstance(claims, list) or not claims or any(x not in FACT_FIELDS for x in claims):
            raise ValueError('Source supports must name factual fields.')
        covered.update(claims)
    if kind in ('source_checked', 'reviewed'):
        if not entry.get('scientific_name', '').strip():
            raise ValueError('Source-checked or reviewed organisms require a scientific_name.')
        if not entry.get('reviewed_by', '').strip() or not entry.get('reviewed_on'):
            raise ValueError('Source-checked or reviewed organisms require a reviewer and review date.')
        date.fromisoformat(entry['reviewed_on'])
        required = {field for field in FACT_FIELDS if entry.get(field)}
        missing = required - covered
        if not sources or missing:
            raise ValueError(f'Source-checked or reviewed organism has uncited facts: {sorted(missing)}.')
