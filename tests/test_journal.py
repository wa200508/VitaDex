import json
import sqlite3

import pytest

from database import CARD_DB
from journal import JOURNAL_VERSION, JournalError, JournalRepository, JournalSession


def build_card():
    organism = CARD_DB.get_organism('Glowleaf Beetle')
    assert organism is not None
    return CARD_DB.build_card(organism)


def test_missing_journal_loads_as_an_empty_collection(tmp_path):
    repository = JournalRepository(tmp_path / 'journal.sqlite3')

    assert repository.load_cards() == []


def test_journal_round_trip_preserves_card_snapshots_in_sqlite(tmp_path):
    journal_path = tmp_path / 'vitadex' / 'journal.sqlite3'
    original_card = build_card()
    repository = JournalRepository(journal_path)

    repository.save_cards([original_card])

    with sqlite3.connect(journal_path) as connection:
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        rows = connection.execute('SELECT position, card_json FROM cards').fetchall()
    loaded_card = repository.load_cards()[0]

    assert version == JOURNAL_VERSION
    assert rows[0][0] == 0
    assert loaded_card == original_card
    assert loaded_card is not original_card
    assert loaded_card.organism is not original_card.organism


def test_legacy_json_journal_is_migrated_to_sqlite(tmp_path):
    database_path = tmp_path / 'journal.sqlite3'
    legacy_path = tmp_path / 'journal.json'
    original_card = build_card()
    legacy_path.write_text(
        json.dumps(
            {
                'version': JOURNAL_VERSION,
                'cards': [JournalRepository._card_to_dict(original_card)],
            }
        )
    )

    loaded_cards = JournalRepository(database_path, legacy_path=legacy_path).load_cards()

    assert database_path.exists()
    assert loaded_cards == [original_card]


@pytest.mark.parametrize('version', [2, 99])
def test_unsupported_database_versions_are_rejected(tmp_path, version):
    journal_path = tmp_path / 'journal.sqlite3'
    with sqlite3.connect(journal_path) as connection:
        connection.execute(f'PRAGMA user_version = {version}')

    with pytest.raises(JournalError, match='not supported'):
        JournalRepository(journal_path).load_cards()


def test_invalid_card_records_are_rejected(tmp_path):
    journal_path = tmp_path / 'journal.sqlite3'
    with sqlite3.connect(journal_path) as connection:
        connection.execute(
            'CREATE TABLE cards (position INTEGER PRIMARY KEY, card_json TEXT NOT NULL)'
        )
        connection.execute('PRAGMA user_version = 1')
        connection.execute('INSERT INTO cards(position, card_json) VALUES (0, ?)', ('{}',))

    with pytest.raises(JournalError, match='invalid card'):
        JournalRepository(journal_path).load_cards()


def test_unreadable_journal_is_not_overwritten_by_new_cards(tmp_path):
    path = tmp_path / 'journal.sqlite3'
    original = b'not a sqlite database'
    path.write_bytes(original)
    session = JournalSession(JournalRepository(path))

    assert session.error is not None
    with pytest.raises(JournalError, match='kept unchanged'):
        session.add_card(build_card())

    assert path.read_bytes() == original
    assert session.cards == []


def test_failed_save_does_not_add_a_card_to_the_session(tmp_path, monkeypatch):
    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    session = JournalSession(repository)

    def fail_save(cards):
        raise JournalError('disk full')

    monkeypatch.setattr(repository, 'save_cards', fail_save)
    with pytest.raises(JournalError, match='disk full'):
        session.add_card(build_card())
    assert session.cards == []
    assert repository.load_cards() == []


def test_successful_save_updates_both_session_and_storage(tmp_path):
    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    session = JournalSession(repository)
    card = build_card()

    session.add_card(card)

    assert session.cards == [card]
    assert repository.load_cards() == [card]


def test_filesystem_errors_are_reported_as_journal_errors(tmp_path):
    parent = tmp_path / 'not_a_directory'
    parent.write_text('occupied')
    repository = JournalRepository(parent / 'journal.sqlite3')

    with pytest.raises(JournalError, match='Could not read journal'):
        repository.load_cards()
    with pytest.raises(JournalError, match='Could not save journal'):
        repository.save_cards([build_card()])
