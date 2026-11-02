from copy import deepcopy
from datetime import date
from dataclasses import replace
import json
import sqlite3

import pytest

from corpus import Corpus, build_corpus, snapshot_context
from database import CARD_DB, DATA_PATH
from editorial import apply_review, review_packet
from diagnostics import DeviceTrace
from journal import JournalError, JournalRepository, JournalSession


def catalog():
    return json.loads(DATA_PATH.read_text())


def approved_packet(data):
    packet = review_packet(data)
    for review in packet['entries']:
        review.update(decision='approved', reviewer_kind='human', reviewer='Test reviewer',
                      reviewed_on=date.today().isoformat())
        review['checks'] = dict.fromkeys(review['checks'], True)
    return packet


def test_packet_starts_pending_and_does_not_promote_anyone():
    data = catalog()
    packet = review_packet(data)
    assert all(r['decision'] == 'pending' and not r['reviewer'] for r in packet['entries'])
    assert apply_review(data, packet) == data


def test_declared_human_review_is_version_bound():
    data = catalog()
    packet = approved_packet(data)
    assert all(x['content_kind'] == 'reviewed' for x in apply_review(data, packet)['organisms'])
    data['organisms'][0]['description'] += ' Changed.'
    with pytest.raises(ValueError, match='Stale'):
        apply_review(data, packet)


@pytest.mark.parametrize('mutation', [
    lambda p: p['entries'][0].update(reviewer_kind='ai'),
    lambda p: p['entries'][0]['checks'].update(child_readability=False),
    lambda p: p['entries'][0]['claims']['description'].update(text='Unrelated claim'),
])
def test_incomplete_or_misleading_reviews_are_rejected(mutation):
    data = catalog()
    packet = approved_packet(data)
    mutation(packet)
    with pytest.raises(ValueError):
        apply_review(data, packet)


def test_corpus_has_separate_original_editorial_passages_and_explicit_preview_gate():
    data = catalog()
    corpus = Corpus(data, build_corpus(data))
    assert corpus.retrieve('taxon:dog', 'What jobs can a dog help people with?') == []
    evidence = corpus.retrieve('taxon:dog', 'What jobs can a dog help people with?', allow_source_checked=True)
    assert evidence and all(p['organism_id'] == 'taxon:dog' for p in evidence)
    assert all(p['kind'] == 'editorial_summary' and p['source_ids'] for p in evidence)
    assert not corpus.retrieve('taxon:dog', 'What is the speed of light?', allow_source_checked=True)
    assert not corpus.retrieve('taxon:cat', 'Can I treat a cat bite?', allow_source_checked=True)


def test_corpus_tamper_and_source_update_require_rebuild():
    data = catalog()
    content = build_corpus(data)
    changed = deepcopy(content)
    changed['passages'][0]['text'] = 'Invented text'
    with pytest.raises(ValueError):
        Corpus(data, changed)
    data['organisms'][0]['sources'][0]['accessed_on'] = '2026-11-01'
    with pytest.raises(ValueError):
        Corpus(data, content)


def test_explicit_card_update_archives_sources_and_preserves_discovery(tmp_path):
    repo = JournalRepository(tmp_path / 'journal.sqlite3')
    session = JournalSession(repo)
    original = CARD_DB.build_card(CARD_DB.organisms['Dog'])
    saved, first = session.discover_card(original)
    changed = replace(original.organism, description=original.organism.description + ' New edition.')
    replacement = CARD_DB.build_card(changed)
    session.update_card(saved, replacement)
    assert len(session.cards) == 1
    assert repo.load_cards()[0] == replacement
    assert not session.discover_card(original)[1]
    with sqlite3.connect(repo.path) as db:
        archived = json.loads(db.execute('SELECT card_json FROM card_history').fetchone()[0])
    assert archived['organism']['description'] == original.organism.description
    assert snapshot_context(original, 'description')['text'] != snapshot_context(replacement, 'description')['text']
    with pytest.raises(JournalError, match='reopen'):
        repo.update_card(original, replacement)


def test_diagnostics_opt_in_bounded_and_omit_text(tmp_path):
    trace = DeviceTrace(tmp_path)
    trace.record('test', text='private')
    trace.flush()
    assert not (tmp_path / 'device-trace.json').exists()
    trace = DeviceTrace(tmp_path, enabled=True, capacity=2)
    for i in range(4):
        trace.record('speech.requested', utterance_id=i, text='not recorded')
    trace.flush()
    result = json.loads((tmp_path / 'device-trace.json').read_text())
    assert len(result['events']) == 2
    assert 'not recorded' not in json.dumps(result)


def test_bundled_retrieval_evaluation_and_references():
    from pathlib import Path
    corpus = Corpus.bundled()
    examples = json.loads((Path(__file__).parents[1] / 'data/corpus-evaluation.json').read_text())
    for case in examples['supported_preview_questions']:
        found = corpus.retrieve(case['organism_id'], case['question'], allow_source_checked=True)
        assert any(passage['field'] == case['field'] for passage in found), case
        assert all(corpus.references(passage) for passage in found)
    for case in examples['unsupported_questions']:
        assert not corpus.retrieve(case['organism_id'], case['question'], allow_source_checked=True), case


def test_existing_legacy_snapshot_can_be_updated_without_rewriting_history(tmp_path):
    repo = JournalRepository(tmp_path / 'journal.sqlite3')
    saved = CARD_DB.build_card(CARD_DB.organisms['Dog'])
    repo.save_cards([saved])
    with sqlite3.connect(repo.path) as db:
        old = repo._card_to_dict(saved)
        old['organism'].pop('organism_id')
        db.execute('UPDATE cards SET card_json = ?', (json.dumps(old),))
    session = JournalSession(repo)
    original = session.cards[0]
    replacement = CARD_DB.build_card(CARD_DB.organisms['Dog'])
    session.update_card(original, replacement)
    assert session.cards == [replacement]
    with sqlite3.connect(repo.path) as db:
        historical = json.loads(db.execute('SELECT card_json FROM card_history').fetchone()[0])
        assert 'organism_id' not in historical['organism']


def test_diagnostics_write_failure_does_not_break_application(tmp_path, monkeypatch):
    import diagnostics
    trace = DeviceTrace(tmp_path, enabled=True)
    trace.record('app.pause')
    def fail(*args):
        raise OSError('Read-only storage')
    monkeypatch.setattr(diagnostics, 'atomic_json', fail)
    assert trace.flush() is False
