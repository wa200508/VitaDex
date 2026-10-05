"""Publication checks; these enforce recorded review, not scientific truth."""

from datetime import date
from urllib.parse import urlparse

from database import CardDatabase

FACT_FIELDS = ('description', 'habitat', 'environment_role', 'physical_dimensions',
               'habitat_type', 'safety_message', 'notes')


def validate_publication(data: dict, reviews: dict) -> None:
    """Reject draft/demo entries and uncited statements before catalog publication.

    Reviews are editorial records keyed by stable organism ID and are kept separate
    from the client catalog. A trusted human publication process owns these records.
    """
    catalog = CardDatabase.from_json(data)
    ids = set()
    model_labels = set()
    for entry in catalog.organisms.values():
        if not entry.id or entry.id in ids:
            raise ValueError('Publication requires unique stable organism IDs.')
        ids.add(entry.id)
        if not isinstance(entry.model_labels, list) or any(
                not isinstance(label, str) or not label for label in entry.model_labels):
            raise ValueError(f'{entry.id}: invalid model labels.')
        for label in entry.model_labels:
            if label in model_labels:
                raise ValueError(f'{entry.id}: ambiguous model label {label}.')
            model_labels.add(label)
        if not isinstance(entry.fact_sources, dict) or not isinstance(entry.references, list):
            raise ValueError(f'{entry.id}: invalid source metadata.')
        if not all(isinstance(getattr(entry, field), str) for field in FACT_FIELDS):
            raise ValueError(f'{entry.id}: fact fields must be text.')
        if entry.is_demo or entry.review_status != 'reviewed':
            raise ValueError(f'{entry.id}: only reviewed non-demo entries may be published.')
        if type(entry.revision) is not int or entry.revision < 1:
            raise ValueError(f'{entry.id}: invalid revision.')
        review = reviews.get(entry.id, {})
        if (review.get('revision') != entry.revision or not review.get('reviewer')
                or not review.get('author') or review['reviewer'] == review['author']
                or review.get('decision') != 'approved'):
            raise ValueError(f'{entry.id}: independent approval of this revision is required.')
        try:
            reviewed_on = date.fromisoformat(review.get('date', ''))
            if reviewed_on > date.today():
                raise ValueError('Future review date')
        except (ValueError, TypeError) as error:
            raise ValueError(f'{entry.id}: invalid review date.') from error
        for field in FACT_FIELDS:
            if not getattr(entry, field):
                continue
            sources = entry.fact_sources.get(field, [])
            if not isinstance(sources, list) or not sources:
                raise ValueError(f'{entry.id}: missing sources for {field}.')
            for source in sources:
                if not isinstance(source, str):
                    raise ValueError(f'{entry.id}: invalid source.')
                parsed = urlparse(source)
                if parsed.scheme != 'https' or not parsed.hostname or source not in entry.references:
                    raise ValueError(f'{entry.id}: sources must be declared HTTPS references.')


def main():
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description='Check a catalog before scientific publication.')
    parser.add_argument('catalog', type=Path)
    parser.add_argument('reviews', type=Path)
    args = parser.parse_args()
    try:
        validate_publication(json.loads(args.catalog.read_text()), json.loads(args.reviews.read_text()))
    except (ValueError, TypeError, KeyError, OSError) as error:
        parser.exit(1, f'Publication rejected: {error}\n')
    print('Publication metadata checks passed; scientific assessment remains the reviewers’ responsibility.')


if __name__ == '__main__':
    main()
