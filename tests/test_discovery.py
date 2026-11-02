from dataclasses import replace

import pytest

from database import DEMO_DB as CARD_DB
from discovery import DiscoveryService, introduction
from identification import IdentificationCandidate, IdentificationResult
from journal import JournalError, JournalRepository, JournalSession


def encounter(organism=None, confidence=1.0):
    organism = organism or next(iter(CARD_DB.organisms.values()))
    return IdentificationResult((IdentificationCandidate(organism, confidence),), source='test')


def test_first_discovery_is_saved_and_repeats_survive_restart(tmp_path):
    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    session = JournalSession(repository)
    service = DiscoveryService(CARD_DB, session)
    first = service.encounter(encounter())
    assert first.is_first
    assert first.narration.startswith(first.card.title + '.')
    assert 'Fictional demo creature' in first.narration
    assert session.cards == [first.card]
    assert not service.encounter(encounter()).is_first
    restarted = DiscoveryService(CARD_DB, JournalSession(repository))
    again = restarted.encounter(encounter())
    assert not again.is_first
    assert again.card == first.card
    assert len(repository.load_cards()) == 1


def test_seen_badge_does_not_reset_discovery_history(tmp_path):
    session = JournalSession(JournalRepository(tmp_path / 'journal.sqlite3'))
    service = DiscoveryService(CARD_DB, session)
    service.encounter(encounter())
    session.mark_seen()
    assert not service.encounter(encounter()).is_first
    assert not session.new_cards


def test_uncertain_or_unknown_encounters_do_not_create_cards(tmp_path):
    session = JournalSession(JournalRepository(tmp_path / 'journal.sqlite3'))
    service = DiscoveryService(CARD_DB, session)
    assert service.encounter(encounter(confidence=.3)) is None
    assert service.encounter(IdentificationResult((), source='test')) is None
    assert session.cards == []


def test_failed_write_does_not_consume_first_discovery(tmp_path, monkeypatch):
    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    session = JournalSession(repository)
    service = DiscoveryService(CARD_DB, session)
    original = repository.append_card
    def fail(_, **kwargs):
        raise JournalError('Disk full')
    monkeypatch.setattr(repository, 'append_card', fail)
    with pytest.raises(JournalError):
        service.encounter(encounter())
    assert not session.cards
    monkeypatch.setattr(repository, 'append_card', original)
    assert service.encounter(encounter()).is_first


def test_legacy_card_is_recognized_without_inventing_facts(tmp_path):
    repository = JournalRepository(tmp_path / 'journal.sqlite3')
    organism = next(iter(CARD_DB.organisms.values()))
    card = CARD_DB.build_card(organism)
    card.organism = replace(organism, content_kind='unreviewed')
    repository.save_cards([card])
    service = DiscoveryService(CARD_DB, JournalSession(repository))
    known = service.encounter(encounter(organism))
    assert not known.is_first
    assert 'not been source reviewed' in introduction(known.card)
    assert organism.description not in introduction(known.card)


def test_voice_preference_survives_restart(tmp_path):
    path = tmp_path / 'journal.sqlite3'
    repository = JournalRepository(path)
    assert repository.load_voice_enabled()
    repository.save_setting('voice_enabled', 0)
    assert not JournalRepository(path).load_voice_enabled()
