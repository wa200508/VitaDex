import hashlib
import io

import pytest

import download_identification_model as downloader


def test_verified_existing_model_requires_no_network(tmp_path, monkeypatch):
    payload = b'verified model'
    target = tmp_path / downloader.MODEL_FILENAME
    target.write_bytes(payload)
    monkeypatch.setattr(downloader, 'MODEL_SHA256', hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(downloader, 'urlopen', lambda *_args, **_kwargs: pytest.fail('unexpected network'))
    assert downloader.download_model(tmp_path) == target


def test_download_is_verified_before_atomic_install(tmp_path, monkeypatch):
    payload = b'new model'
    monkeypatch.setattr(downloader, 'MODEL_SHA256', hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(downloader, 'urlopen', lambda *_args, **_kwargs: io.BytesIO(payload))
    target = downloader.download_model(tmp_path)
    assert target.read_bytes() == payload
    assert not list(tmp_path.glob('*.part'))


def test_failed_checksum_does_not_replace_existing_file(tmp_path, monkeypatch):
    target = tmp_path / downloader.MODEL_FILENAME
    target.write_bytes(b'original')
    monkeypatch.setattr(downloader, 'MODEL_SHA256', hashlib.sha256(b'expected').hexdigest())
    monkeypatch.setattr(downloader, 'urlopen', lambda *_args, **_kwargs: io.BytesIO(b'wrong'))
    with pytest.raises(ValueError, match='checksum'):
        downloader.download_model(tmp_path)
    assert target.read_bytes() == b'original'
    assert not list(tmp_path.glob('*.part'))


def test_network_failure_removes_partial_download(tmp_path, monkeypatch):
    def fail(*_args, **_kwargs):
        raise OSError('connection failed')
    monkeypatch.setattr(downloader, 'urlopen', fail)
    with pytest.raises(OSError, match='connection failed'):
        downloader.download_model(tmp_path)
    assert list(tmp_path.iterdir()) == []
