from threading import Event
import json
from pathlib import Path

import pytest

from ask import answer_card, AskError, SessionProvider
from database import CARD_DB, DATA_PATH
from scripts import sync_card_db as sync


def dog():
    return CARD_DB.build_card(CARD_DB.organisms['Dog'])


def test_offline_review_gate_and_citations():
    assert not answer_card(dog(), 'What jobs can dogs help people with?').passages
    answer = answer_card(dog(), 'What jobs can dogs help people with?', allow_source_checked=True)
    assert answer.passages and answer.references and answer.provisional
    assert all('dog' in p['organism_id'] for p in answer.passages)
    assert not answer_card(dog(), 'Can I treat a dog bite?', allow_source_checked=True).passages


@pytest.mark.parametrize('response', [
    {'passage_ids': ['invented']}, {'passage_ids': [{}]},
    {'answer': 'Dogs are made of gold', 'passage_ids': []},
])
def test_provider_cannot_inject_uncited_text_or_fake_ids(response):
    class Provider:
        def select(self, *args):
            return response
    with pytest.raises(AskError):
        answer_card(dog(), 'What jobs can dogs help people with?', Provider(), True)


def test_model_sees_only_retrieved_data_and_can_only_select_existing_evidence():
    class Provider:
        def select(self, question, passages, cancel):
            assert len(passages) <= 3
            return {'passage_ids': [passages[0]['id']]}
    answer = answer_card(dog(), 'What jobs can dogs help people with?', Provider(), True)
    assert len(answer.passages) == 1
    assert answer.text.startswith(answer.passages[0]['text'])
    cancel = Event()
    cancel.set()
    with pytest.raises(AskError, match='cancelled'):
        answer_card(dog(), 'jobs', Provider(), True, cancel)


@pytest.mark.parametrize('endpoint', ['http://provider.test/v1', 'https://key@provider.test/v1', 'https://provider.test/v1?key=x'])
def test_provider_endpoint_rejects_unsafe_credential_locations(endpoint):
    with pytest.raises(AskError):
        SessionProvider(endpoint, 'model', 'key')


def test_atomic_catalog_replacement_recovers_from_corrupt_current(tmp_path, monkeypatch):
    data = json.loads(DATA_PATH.read_text())
    monkeypatch.setattr(sync, 'download_json', lambda *args: data)
    target = tmp_path / 'database.json'
    target.write_bytes(b'broken JSON')
    sync.sync_catalog('https://example.test/catalog', target, DATA_PATH.parent.parent / 'card_database_schema.json')
    assert json.loads(target.read_text()) == data
    assert target.with_name('database.json.bak').read_bytes() == b'broken JSON'


def test_interrupted_replacement_preserves_current_and_backup(tmp_path, monkeypatch):
    target = tmp_path / 'database.json'
    original = DATA_PATH.read_bytes()
    target.write_bytes(original)
    monkeypatch.setattr(sync, 'download_json', lambda *args: json.loads(original))
    replace = sync.os.replace
    def fail(source, destination):
        if Path(destination) == target:
            raise OSError('Simulated interrupted rename')
        return replace(source, destination)
    monkeypatch.setattr(sync.os, 'replace', fail)
    with pytest.raises(OSError):
        sync.sync_catalog('https://example.test/catalog', target, DATA_PATH.parent.parent / 'card_database_schema.json')
    assert target.read_bytes() == original
    assert target.with_name('database.json.bak').read_bytes() == original


def test_download_timeout_and_invalid_payload_never_replace(tmp_path, monkeypatch):
    def timeout(*args, **kwargs):
        assert kwargs['timeout'] == 15
        raise TimeoutError('offline')
    monkeypatch.setattr(sync, 'urlopen', timeout)
    with pytest.raises(TimeoutError):
        sync.download_json('https://example.test/catalog')
    monkeypatch.setattr(sync, 'download_json', lambda *args: {})
    target = tmp_path / 'database.json'
    target.write_bytes(b'original')
    with pytest.raises(Exception):
        sync.sync_catalog('https://example.test/catalog', target, DATA_PATH.parent.parent / 'card_database_schema.json')
    assert target.read_bytes() == b'original'


def test_provider_transport_bounds_and_secret_redaction(monkeypatch):
    import ask
    seen = []
    class Response:
        def __init__(self, payload):
            self.payload = payload
            self.closed = False
        def read1(self, size):
            data, self.payload = self.payload[:size], self.payload[size:]
            return data
        def close(self):
            self.closed = True
    response = Response(json.dumps({'choices': [{'message': {'content': json.dumps({'passage_ids': ['p']})}}]}).encode())
    class Opener:
        def open(self, request, timeout):
            seen.append(request)
            assert timeout == 15
            return response
    monkeypatch.setattr(ask, 'build_opener', lambda *args: Opener())
    provider = SessionProvider('https://provider.test/v1/chat/completions', 'chosen-model', 'test-secret')
    assert provider.select('question', [{'id': 'p', 'text': 'evidence'}], Event()) == {'passage_ids': ['p']}
    body = json.loads(seen[0].data)
    assert body['max_tokens'] == 256 and len(body['messages']) == 2
    assert response.closed
    provider.clear()
    assert not provider.key
    class Failing:
        def open(self, *args, **kwargs):
            raise OSError('provider returned test-secret')
    monkeypatch.setattr(ask, 'build_opener', lambda *args: Failing())
    with pytest.raises(AskError) as error:
        SessionProvider('https://provider.test/v1', 'model', 'test-secret').select('q', [], Event())
    assert 'test-secret' not in str(error.value)


def test_no_provider_call_without_supported_evidence():
    class Provider:
        def select(self, *args):
            raise AssertionError('No network work should be requested')
    assert not answer_card(dog(), 'What is the speed of light?', Provider(), True).passages
