import json
import sqlite3
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from database import CARD_DB, DEMO_DB, DATA_PATH, CardDatabase
from discovery import DiscoveryService
from identification import IdentificationCandidate, IdentificationResult
from journal import JournalError, JournalRepository, JournalSession


def card():
    return DEMO_DB.build_card(next(iter(DEMO_DB.organisms.values())))


def legacy(path):
    path.write_text(json.dumps({'version': 1, 'cards': [JournalRepository._card_to_dict(card())]}))


def test_interrupted_migration_retries_existing_empty_file(tmp_path):
    path, old = tmp_path / 'journal.sqlite3', tmp_path / 'journal.json'
    legacy(old)
    sqlite3.connect(path).close()
    repo = JournalRepository(path, old)
    assert len(repo.load_cards()) == 1
    assert len(repo.load_cards()) == 1
    assert old.exists()
    repo.save_cards([])  # An intentional empty collection must not resurrect the backup.
    assert not repo.load_cards()


def test_migration_failure_rolls_back_and_next_start_retries(tmp_path):
    path, old = tmp_path / 'journal.sqlite3', tmp_path / 'journal.json'
    legacy(old)
    repo = JournalRepository(path, old)
    with sqlite3.connect(path) as db:
        repo._initialize(db)
        db.execute("CREATE TRIGGER fail_import BEFORE INSERT ON cards BEGIN SELECT RAISE(ABORT, 'full'); END")
    with pytest.raises(JournalError):
        repo.load_cards()
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM cards').fetchone()[0] == 0
        assert not db.execute("SELECT 1 FROM journal_settings WHERE key='migration_complete'").fetchone()
        db.execute('DROP TRIGGER fail_import')
    assert len(repo.load_cards()) == 1


def test_existing_populated_database_is_not_merged_with_legacy(tmp_path):
    old = tmp_path / 'journal.json'
    legacy(old)
    repo = JournalRepository(tmp_path / 'journal.sqlite3', old)
    first = card()
    repo.save_cards([first, first])
    assert repo.load_cards() == [first, first]


def match(organism):
    return IdentificationResult((IdentificationCandidate(organism, 1.0),), source='test')


def test_species_aliases_and_renamed_display_names_preserve_discovery(tmp_path):
    repo = JournalRepository(tmp_path / 'journal.sqlite3')
    dog = CARD_DB.organisms['Dog']
    assert DiscoveryService(CARD_DB, JournalSession(repo)).encounter(match(dog)).is_first
    alias = replace(dog, name='Domestic Dog', scientific_name='Canis familiaris', organism_id='')
    result = DiscoveryService(CARD_DB, JournalSession(repo)).encounter(match(alias))
    assert not result.is_first
    assert result.card.title == 'Dog'
    assert len(repo.load_cards()) == 1


def test_two_sessions_claim_only_one_first_discovery(tmp_path):
    path = tmp_path / 'journal.sqlite3'
    services = [DiscoveryService(CARD_DB, JournalSession(JournalRepository(path))) for _ in range(2)]
    barrier = Barrier(2)
    def discover(service):
        barrier.wait(timeout=3)
        return service.encounter(match(CARD_DB.organisms['Dog']))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(discover, services))
    assert sum(result.is_first for result in results) == 1
    assert len(JournalRepository(path).load_cards()) == 1


@pytest.mark.parametrize('field,value', [('description', 17), ('type', []), ('sources', 'bad')])
def test_direct_catalog_load_rejects_types_before_ui(field, value):
    data = json.loads(DATA_PATH.read_text())
    data['organisms'][0][field] = value
    with pytest.raises(ValueError):
        CardDatabase.from_json(data)


def test_source_mapped_display_cannot_drift(tmp_path):
    repo = JournalRepository(tmp_path / 'journal.sqlite3')
    valid = card()
    repo.save_cards([valid])
    invalid = card()
    invalid.selected_details['Habitat'] = 'Unsupported location'
    with pytest.raises(JournalError):
        repo.append_card(invalid)
    assert repo.load_cards() == [valid]


def test_normal_addition_does_not_rewrite_existing_cards(tmp_path):
    statements = []
    class TracedRepository(JournalRepository):
        def _connect(self):
            db = super()._connect()
            db.set_trace_callback(statements.append)
            return db
    repo = TracedRepository(tmp_path / 'journal.sqlite3')
    repo.save_cards([card() for _ in range(100)])
    session = JournalSession(repo)
    statements.clear()
    session.add_card(card())
    writes = [sql for sql in statements if sql.upper().startswith(('INSERT INTO CARDS', 'UPDATE CARDS', 'DELETE FROM CARDS'))]
    assert len(writes) == 1
    assert len(repo.load_cards()) == 101
