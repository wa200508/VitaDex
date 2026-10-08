from queue import Queue
from threading import Event

from catalog_jobs import CatalogUpdateWorker
from catalog_updates import CATALOG_MANIFEST_URL, CatalogCache


def test_check_is_explicit_single_flight_and_delivered_on_ui_thread(tmp_path):
    started, release = Event(), Event()
    scheduled, results = Queue(), []
    def update(url, cache):
        assert url == CATALOG_MANIFEST_URL
        started.set()
        assert release.wait(5)
        return 2
    worker = CatalogUpdateWorker(CatalogCache(tmp_path), scheduled.put, update)
    assert not started.is_set()
    assert not worker.cache.path.exists()
    assert worker.start(lambda *args: results.append(args), results.append)
    assert started.wait(5)
    assert not worker.start(lambda *_: None, lambda *_: None)
    release.set()
    callback = scheduled.get(timeout=5)
    assert results == []
    callback()
    assert results == [(2, True)]
    assert not worker.busy
    worker.close()


def test_failure_resets_check_and_shutdown_suppresses_callbacks(tmp_path):
    scheduled, errors = Queue(), []
    def fail(*_):
        raise OSError('offline')
    worker = CatalogUpdateWorker(CatalogCache(tmp_path), scheduled.put, fail)
    assert worker.start(lambda *_: None, errors.append)
    scheduled.get(timeout=5)()
    assert errors == ['offline']
    assert not worker.busy
    assert worker.start(lambda *_: None, errors.append)
    callback = scheduled.get(timeout=5)
    worker.close()
    callback()
    assert errors == ['offline']
    assert not worker.start(lambda *_: None, errors.append)
