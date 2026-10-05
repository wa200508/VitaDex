"""Versioned SQLite storage for a VitaDex card journal."""

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Optional

from database import Card, CardBackground, OrganismEntry


JOURNAL_VERSION = 2


class JournalError(ValueError):
    """Raised when a journal cannot be safely read or written."""


class JournalRepository:
    """Persist card snapshots in a local SQLite database without an account."""

    def __init__(self, path: Path, legacy_path: Optional[Path] = None):
        self.path = Path(path)
        self.legacy_path = Path(legacy_path) if legacy_path else None

    def load_cards(self) -> List[Card]:
        """Load cards, migrating a prior JSON journal the first time it is used."""
        if not self.path.exists() and self.legacy_path and self.legacy_path.exists():
            cards = self._load_legacy_cards()
            self.save_cards(cards)
            return cards

        try:
            with closing(self._connect()) as connection, connection:
                self._initialize(connection)
                rows = connection.execute(
                    'SELECT card_json FROM cards ORDER BY position ASC'
                ).fetchall()
        except (sqlite3.Error, OSError) as error:
            raise JournalError(f'Could not read journal at {self.path}: {error}') from error

        try:
            return [self._card_from_dict(json.loads(row['card_json'])) for row in rows]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise JournalError(f'Journal contains an invalid card: {error}') from error

    def save_cards(self, cards: Iterable[Card]) -> None:
        """Replace the collection in one SQLite transaction."""
        serialized_cards = [json.dumps(self._card_to_dict(card), ensure_ascii=False) for card in cards]

        try:
            with closing(self._connect()) as connection, connection:
                self._initialize(connection)
                connection.execute('DELETE FROM cards')
                connection.executemany(
                    'INSERT INTO cards(position, card_json) VALUES (?, ?)',
                    enumerate(serialized_cards),
                )
        except (sqlite3.Error, OSError) as error:
            raise JournalError(f'Could not save journal at {self.path}: {error}') from error

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _initialize(connection: sqlite3.Connection) -> None:
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, 1, JOURNAL_VERSION):
            raise JournalError(f'Journal database version {version} is not supported.')

        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS cards (
                position INTEGER PRIMARY KEY,
                card_json TEXT NOT NULL
            )
            '''
        )
        if version < JOURNAL_VERSION:
            connection.execute(f'PRAGMA user_version = {JOURNAL_VERSION}')

    def _load_legacy_cards(self) -> List[Card]:
        assert self.legacy_path is not None
        try:
            data = json.loads(self.legacy_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as error:
            raise JournalError(f'Could not read legacy journal at {self.legacy_path}: {error}') from error

        if not isinstance(data, dict) or data.get('version') not in (1, JOURNAL_VERSION):
            raise JournalError('Legacy journal has an unsupported or missing version.')
        cards = data.get('cards')
        if not isinstance(cards, list):
            raise JournalError('Legacy journal cards must be a list.')

        try:
            return [self._card_from_dict(card) for card in cards]
        except (KeyError, TypeError, ValueError) as error:
            raise JournalError(f'Legacy journal contains an invalid card: {error}') from error

    @staticmethod
    def _card_to_dict(card: Card) -> dict:
        return {
            'organism': asdict(card.organism),
            'background': asdict(card.background),
            'art_asset': card.art_asset,
            'selected_moves': card.selected_moves,
            'selected_details': card.selected_details,
            'encounter_id': card.encounter_id,
            'observed_at': card.observed_at,
            'photo_asset': card.photo_asset,
            'local_art_asset': card.local_art_asset,
            'identification_source': card.identification_source,
            'confidence': card.confidence,
        }

    @staticmethod
    def _card_from_dict(data: dict) -> Card:
        if not isinstance(data, dict):
            raise ValueError('Card must be an object.')
        return Card(
            organism=OrganismEntry(**data['organism']),
            background=CardBackground(**data['background']),
            art_asset=data['art_asset'],
            selected_moves=data['selected_moves'],
            selected_details=data['selected_details'],
            encounter_id=data.get('encounter_id', ''),
            observed_at=data.get('observed_at', ''),
            photo_asset=data.get('photo_asset', ''),
            local_art_asset=data.get('local_art_asset', ''),
            identification_source=data.get('identification_source', 'legacy'),
            confidence=data.get('confidence'),
        )


class JournalSession:
    """Keep the displayed collection consistent with durable local storage."""

    def __init__(self, repository: JournalRepository):
        self.repository = repository
        self.error = None
        try:
            self.cards = repository.load_cards()
        except JournalError as error:
            self.cards = []
            self.error = str(error)

    def add_card(self, card: Card) -> None:
        if self.error is not None:
            raise JournalError(
                'The existing journal could not be read. It has been kept unchanged. '
                'Restore the journal before adding cards.'
            )
        updated_cards = [*self.cards, card]
        self.repository.save_cards(updated_cards)
        self.cards.append(card)
