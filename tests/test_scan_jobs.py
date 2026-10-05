from queue import Queue
from threading import Event

import pytest
from PIL import Image

from identification import IdentificationResult
from photos import PhotoStore
from scan_jobs import ScanWorker


class Service:
    def identify(self, encounter):
        return IdentificationResult((), 'local-test')


def setup_worker(tmp_path, service=None):
    photo = tmp_path / 'source.jpg'
    Image.new('RGB', (40, 40), 'red').save(photo)
    scheduled = Queue()
    worker = ScanWorker(PhotoStore(tmp_path / 'photos'), service or Service(), scheduled.put)
    return worker, photo, scheduled


def test_scan_is_delivered_only_through_the_ui_scheduler(tmp_path):
    worker, photo, scheduled = setup_worker(tmp_path)
    received = []
    assert worker.start(photo, lambda *args: received.append(args), received.append, lambda: None)
    assert not worker.start(photo, lambda *_: None, lambda _: None, lambda: None)
    callback = scheduled.get(timeout=5)
    assert received == []
    callback()
    assert len(received) == 1
    assert received[0][0].photo_path.is_file()
    assert not worker.busy
    worker.close()


def test_cancelled_scan_never_delivers_a_match_and_discards_owned_photo(tmp_path):
    worker, photo, scheduled = setup_worker(tmp_path)
    received = []
    cancelled = []
    worker.start(photo, lambda *args: received.append(args), received.append, lambda: cancelled.append(True))
    callback = scheduled.get(timeout=5)
    worker.cancel()
    callback()
    assert received == []
    assert cancelled == [True]
    assert not list(worker.photo_store.directory.glob('*.jpg'))
    assert photo.is_file()
    worker.close()


def test_provider_failure_discards_owned_photo_and_reports_error(tmp_path):
    class FailedService:
        def identify(self, encounter):
            raise ValueError('model unavailable')
    worker, photo, scheduled = setup_worker(tmp_path, FailedService())
    errors = []
    worker.start(photo, lambda *_: None, errors.append, lambda: None)
    scheduled.get(timeout=5)()
    assert str(errors[0]) == 'model unavailable'
    assert not list(worker.photo_store.directory.glob('*.jpg'))
    worker.close()


def test_shutdown_discards_running_scan_without_scheduling_ui_work(tmp_path):
    started, release = Event(), Event()
    class BlockingService:
        def identify(self, encounter):
            started.set()
            assert release.wait(timeout=5)
            return IdentificationResult((), 'test')
    worker, photo, scheduled = setup_worker(tmp_path, BlockingService())
    worker.start(photo, lambda *_: None, lambda _: None, lambda: None)
    assert started.wait(timeout=5)
    worker.close()
    release.set()
    worker.executor.shutdown(wait=True)
    assert scheduled.empty()
    assert not list(worker.photo_store.directory.glob('*.jpg'))
    assert not worker.start(photo, lambda *_: None, lambda _: None, lambda: None)


def test_art_is_created_after_recognition_and_cancelled_with_photo(tmp_path):
    from database import NATURE_DB
    from identification import IdentificationCandidate

    class MatchService:
        def identify(self, encounter):
            assert encounter.art_path is None
            return IdentificationResult(
                (IdentificationCandidate(next(iter(NATURE_DB.organisms.values())), .9),),
                'local-test',
            )

    worker, photo, scheduled = setup_worker(tmp_path, MatchService())
    worker.start(photo, lambda *_: None, lambda error: pytest.fail(str(error)), lambda: None)
    callback = scheduled.get(timeout=5)
    assert list(worker.photo_store.directory.glob('*-art.jpg'))
    worker.cancel()
    callback()
    assert not list(worker.photo_store.directory.glob('*.jpg'))
    worker.close()
