import json
import sqlite3

import pytest

from database import DEMO_DB as CARD_DB
from journal import JOURNAL_VERSION, JournalError, JournalRepository


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


def test_unreadable_journal_cannot_be_overwritten_by_session(tmp_path):
    from journal import JournalSession

    path = tmp_path / 'journal.sqlite3'
    original = b'not a sqlite database'
    path.write_bytes(original)
    session = JournalSession(JournalRepository(path))

    assert session.load_error is not None
    with pytest.raises(JournalError, match='No changes were saved'):
        session.add_card(build_card())
    assert path.read_bytes() == original
    assert session.cards == []


def test_failed_save_does_not_add_a_card_to_session(tmp_path, monkeypatch):
    from journal import JournalSession

    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    original_card = build_card()
    repository.save_cards([original_card])
    session = JournalSession(repository)

    def fail_save(cards, **kwargs):
        raise JournalError('Disk full')

    monkeypatch.setattr(repository, 'append_card', fail_save)
    with pytest.raises(JournalError, match='Disk full'):
        session.add_card(build_card())
    assert session.cards == [original_card]
    assert repository.load_cards() == [original_card]


def test_session_addition_survives_restart(tmp_path):
    from journal import JournalSession

    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    session = JournalSession(repository)
    card = build_card()
    session.add_card(card)

    assert JournalSession(repository).cards == [card]


def test_storage_directory_errors_are_reported_as_journal_errors(tmp_path):
    parent = tmp_path / 'file'
    parent.write_text('not a directory')
    repository = JournalRepository(parent / 'journal.sqlite3')
    with pytest.raises(JournalError):
        repository.load_cards()
    with pytest.raises(JournalError):
        repository.save_cards([build_card()])


def test_new_cards_and_mark_seen_survive_restart(tmp_path):
    from journal import JournalSession

    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    session = JournalSession(repository)
    card = build_card()
    session.add_card(card)
    restarted = JournalSession(repository)
    assert restarted.new_cards == [card]
    restarted.mark_seen()
    assert JournalSession(repository).new_cards == []
    restarted.add_card(card)
    assert len(JournalSession(repository).new_cards) == 1


def test_failed_mark_seen_preserves_badge_state(tmp_path, monkeypatch):
    from journal import JournalSession

    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    session = JournalSession(repository)
    session.add_card(build_card())

    def fail_save(count):
        raise JournalError('Read-only storage')

    monkeypatch.setattr(repository, 'save_seen_count', fail_save)
    with pytest.raises(JournalError):
        session.mark_seen()
    assert len(session.new_cards) == 1


@pytest.mark.parametrize('field,value', [
    ('selected_moves', 'not a list'),
    ('selected_details', {'Size': '3 cm'}),
    ('organism', {'name': 42}),
    ('art_asset', None),
])
def test_malformed_card_fields_are_rejected_before_ui_load(tmp_path, field, value):
    path = tmp_path / 'journal.sqlite3'
    repository = JournalRepository(path)
    repository.save_cards([build_card()])
    data = repository._card_to_dict(build_card())
    data[field] = value
    with sqlite3.connect(path) as connection:
        connection.execute('UPDATE cards SET card_json = ?', (json.dumps(data),))
    with pytest.raises(JournalError, match='invalid card'):
        repository.load_cards()


def test_invalid_save_preserves_existing_collection(tmp_path):
    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    card = build_card()
    repository.save_cards([card])
    broken = build_card()
    broken.selected_moves = 'bad data'
    with pytest.raises(JournalError, match='invalid card'):
        repository.save_cards([broken])
    assert repository.load_cards() == [card]
