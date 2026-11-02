"""Versioned SQLite storage for a VitaDex card journal."""

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Optional
from threading import RLock

from identity import organism_key
from validation import validate_model

from database import Card, CardBackground, OrganismEntry
from provenance import validate_provenance


JOURNAL_VERSION = 1


class JournalError(ValueError):
    """Raised when a journal cannot be safely read or written."""


class JournalRepository:
    """Persist card snapshots in a local SQLite database without an account."""

    def __init__(self, path: Path, legacy_path: Optional[Path] = None):
        self.path = Path(path)
        self.legacy_path = Path(legacy_path) if legacy_path else None

    def load_cards(self) -> List[Card]:
        """Load cards, migrating a prior JSON journal the first time it is used."""
        try:
            with closing(self._connect()) as connection, connection:
                connection.execute('BEGIN IMMEDIATE')
                self._initialize(connection)
                count = connection.execute('SELECT COUNT(*) FROM cards').fetchone()[0]
                complete = connection.execute(
                    "SELECT value FROM journal_settings WHERE key = 'migration_complete'"
                ).fetchone()
                if not count and not complete and self.legacy_path and self.legacy_path.exists():
                    cards = self._load_legacy_cards()
                    connection.executemany('INSERT INTO cards(position, card_json) VALUES (?, ?)',
                        ((i, self._serialize(card)) for i, card in enumerate(cards)))
                rows = connection.execute('SELECT position, card_json FROM cards ORDER BY position').fetchall()
                cards = [self._card_from_dict(json.loads(row['card_json'])) for row in rows]
                for row, card in zip(rows, cards):
                    connection.execute('INSERT OR IGNORE INTO discoveries VALUES (?, ?)',
                                       (organism_key(card.organism), row['position']))
                connection.execute(
                    "INSERT OR IGNORE INTO journal_settings VALUES ('migration_complete', 1)")
                return cards
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as error:
            raise JournalError(f'Could not read journal or invalid card at {self.path}: {error}') from error

    @classmethod
    def _serialize(cls, card):
        snapshot = cls._card_to_dict(card)
        cls._card_from_dict(snapshot)
        return json.dumps(snapshot, ensure_ascii=False)

    def save_cards(self, cards: Iterable[Card]) -> None:
        """Replace the collection in one SQLite transaction."""
        try:
            snapshots = [self._card_to_dict(card) for card in cards]
            for snapshot in snapshots:
                self._card_from_dict(snapshot)
            serialized_cards = [json.dumps(snapshot, ensure_ascii=False) for snapshot in snapshots]
        except (TypeError, KeyError, ValueError) as error:
            raise JournalError(f'Cannot save an invalid card: {error}') from error

        try:
            with closing(self._connect()) as connection, connection:
                connection.execute('BEGIN IMMEDIATE')
                self._initialize(connection)
                connection.execute('DELETE FROM discoveries')
                connection.execute('DELETE FROM cards')
                connection.executemany(
                    'INSERT INTO cards(position, card_json) VALUES (?, ?)',
                    enumerate(serialized_cards),
                )
                for i, snapshot in enumerate(snapshots):
                    key = organism_key(OrganismEntry(**snapshot['organism']))
                    connection.execute('INSERT OR IGNORE INTO discoveries VALUES (?, ?)', (key, i))
                connection.execute(
                    "INSERT OR IGNORE INTO journal_settings VALUES ('migration_complete', 1)")
        except (sqlite3.Error, OSError) as error:
            raise JournalError(f'Could not save journal at {self.path}: {error}') from error

    def append_card(self, card: Card, unique=False):
        """Append a single snapshot; a unique discovery is claimed in the same transaction."""
        try:
            serialized = self._serialize(card)
            with closing(self._connect()) as connection, connection:
                connection.execute('BEGIN IMMEDIATE')
                self._initialize(connection)
                key = organism_key(card.organism)
                if unique:
                    row = connection.execute(
                        'SELECT card_json FROM cards JOIN discoveries ON position = card_position '
                        'WHERE organism_key = ?', (key,)).fetchone()
                    if row is not None:
                        return self._card_from_dict(json.loads(row[0])), False
                position = connection.execute('SELECT COALESCE(MAX(position), -1) + 1 FROM cards').fetchone()[0]
                connection.execute('INSERT INTO cards VALUES (?, ?)', (position, serialized))
                connection.execute('INSERT OR IGNORE INTO discoveries VALUES (?, ?)', (key, position))
                connection.execute(
                    "INSERT OR IGNORE INTO journal_settings VALUES ('migration_complete', 1)")
                return card, True
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as error:
            raise JournalError(f'Could not append card: {error}') from error

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _initialize(connection: sqlite3.Connection) -> None:
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, JOURNAL_VERSION):
            raise JournalError(f'Journal database version {version} is not supported.')

        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS cards (
                position INTEGER PRIMARY KEY,
                card_json TEXT NOT NULL
            )
            '''
        )
        connection.execute(
            'CREATE TABLE IF NOT EXISTS journal_settings (key TEXT PRIMARY KEY, value INTEGER NOT NULL)'
        )
        connection.execute('CREATE TABLE IF NOT EXISTS discoveries ('
                           'organism_key TEXT PRIMARY KEY, card_position INTEGER NOT NULL)')
        if version == 0:
            connection.execute(f'PRAGMA user_version = {JOURNAL_VERSION}')

    def _load_legacy_cards(self) -> List[Card]:
        assert self.legacy_path is not None
        try:
            data = json.loads(self.legacy_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as error:
            raise JournalError(f'Could not read legacy journal at {self.legacy_path}: {error}') from error

        if not isinstance(data, dict) or data.get('version') != JOURNAL_VERSION:
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
        }

    @staticmethod
    def _card_from_dict(data: dict) -> Card:
        if not isinstance(data, dict):
            raise ValueError('Card must be an object.')
        validate_model(data.get('organism'), OrganismEntry)
        validate_model(data.get('background'), CardBackground)
        validate_provenance(data['organism'])
        if not isinstance(data.get('art_asset'), str):
            raise ValueError('art_asset must be text.')
        moves = data.get('selected_moves')
        if not isinstance(moves, list) or any(not isinstance(x, str) for x in moves):
            raise ValueError('selected_moves must be a list of strings.')
        details = data.get('selected_details')
        if not isinstance(details, dict) or not {'Habitat', 'Size'} <= details.keys():
            raise ValueError('selected_details must include Habitat and Size.')
        if any(not isinstance(value, str) for value in details.values()):
            raise ValueError('selected_details values must be text.')
        organism = OrganismEntry(**data['organism'])
        expected = {'Habitat': organism.habitat_type or organism.habitat,
                    'Size': organism.physical_dimensions or 'Unknown',
                    'Role': organism.environment_role}
        if any(key in details and details[key] != value for key, value in expected.items()):
            raise ValueError('Displayed details differ from the cited organism snapshot.')
        return Card(
            organism=OrganismEntry(**data['organism']),
            background=CardBackground(**data['background']),
            art_asset=data['art_asset'],
            selected_moves=data['selected_moves'],
            selected_details=data['selected_details'],
        )


    def load_seen_count(self) -> int:
        try:
            with closing(self._connect()) as connection, connection:
                self._initialize(connection)
                row = connection.execute(
                    "SELECT value FROM journal_settings WHERE key = 'seen_count'"
                ).fetchone()
                if row is None:
                    # Existing journals predate the badge setting: consider them seen.
                    count = connection.execute('SELECT COUNT(*) FROM cards').fetchone()[0]
                    connection.execute("INSERT INTO journal_settings VALUES ('seen_count', ?)", (count,))
                    return count
                return max(0, int(row[0]))
        except (sqlite3.Error, OSError, ValueError, TypeError) as error:
            raise JournalError(f'Could not read journal settings: {error}') from error

    def load_voice_enabled(self) -> bool:
        try:
            with closing(self._connect()) as connection, connection:
                self._initialize(connection)
                row = connection.execute(
                    "SELECT value FROM journal_settings WHERE key = 'voice_enabled'"
                ).fetchone()
                return bool(row[0]) if row else True
        except (sqlite3.Error, OSError) as error:
            raise JournalError(f'Could not read voice settings: {error}') from error

    def save_setting(self, key: str, value: int) -> None:
        try:
            with closing(self._connect()) as connection, connection:
                self._initialize(connection)
                connection.execute(
                    'INSERT OR REPLACE INTO journal_settings(key, value) VALUES (?, ?)',
                    (key, value),
                )
        except (sqlite3.Error, OSError) as error:
            raise JournalError(f'Could not save journal settings: {error}') from error

    def save_seen_count(self, count: int) -> None:
        self.save_setting('seen_count', count)


class JournalSession:
    """Keep UI state consistent with durable storage and protect unreadable journals."""

    def __init__(self, repository: JournalRepository):
        self.repository = repository
        self.lock = RLock()
        self.revision = 0
        self.by_key = {}
        self.legacy_names = {}
        self._new_cache = (-1, set())
        self.cards = []
        self.load_error = None
        self.seen_count = 0
        try:
            self.cards = repository.load_cards()
            self.seen_count = min(len(self.cards), repository.load_seen_count())
            for card in self.cards:
                self._index_card(card)
        except JournalError as error:
            self.load_error = error

    def add_card(self, card: Card) -> None:
        if self.load_error is not None:
            raise JournalError(
                'The journal could not be opened. No changes were saved. '
                'Back up your journal and resolve the storage error before restarting.'
            ) from self.load_error
        with self.lock:
            self.repository.append_card(card)
            self.cards.append(card)
            self._index_card(card)
            self.revision += 1


    def discover_card(self, card):
        if self.load_error is not None:
            raise JournalError('The journal could not be opened. No changes were saved.')
        with self.lock:
            saved, first = self.repository.append_card(card, unique=True)
            key = organism_key(saved.organism)
            existing = self.by_key.get(key)
            if existing is None:
                self.cards.append(saved)
                self._index_card(saved)
                self.revision += 1
            return existing or saved, first

    def _index_card(self, card):
        self.by_key.setdefault(organism_key(card.organism), card)
        if card.organism.content_kind == 'unreviewed' and not card.organism.scientific_name:
            self.legacy_names.setdefault(card.title.strip().casefold(), card)

    def is_new(self, card):
        if self._new_cache[0] != self.revision:
            self._new_cache = (self.revision, {id(x) for x in self.cards[self.seen_count:]})
        return id(card) in self._new_cache[1]

    @property
    def new_count(self):
        return max(0, len(self.cards) - self.seen_count)

    @property
    def new_cards(self) -> List[Card]:
        return self.cards[self.seen_count:]

    def mark_seen(self) -> None:
        if self.load_error is not None:
            raise JournalError('The journal could not be opened. No changes were saved.')
        self.repository.save_seen_count(len(self.cards))
        self.seen_count = len(self.cards)
        self.revision += 1
