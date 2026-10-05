from queue import Queue
from threading import Event

from database import NATURE_DB
from export_jobs import ExportWorker


def test_export_delivered_on_ui_scheduler(tmp_path):
    scheduled = Queue()
    worker = ExportWorker(tmp_path, scheduled.put)
    card = NATURE_DB.build_card(next(iter(NATURE_DB.organisms.values())))
    received = []
    assert worker.start(card, 'Letter', received.append, received.append)
    assert not worker.start(card, 'Letter', received.append, received.append)
    callback = scheduled.get(timeout=5)
    assert received == []
    callback()
    assert received[0].path.exists()
    assert not worker.busy
    worker.close()


def test_shutdown_discards_generated_file(tmp_path, monkeypatch):
    from print_export import ExportResult
    started, release = Event(), Event()
    def generate(card, root, target, paper):
        started.set()
        assert release.wait(timeout=5)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'PDF')
        return ExportResult(target, ())
    monkeypatch.setattr('print_export.export_card', generate)
    scheduled = Queue()
    worker = ExportWorker(tmp_path, scheduled.put)
    card = NATURE_DB.build_card(next(iter(NATURE_DB.organisms.values())))
    worker.start(card, 'Letter', lambda _: None, lambda _: None)
    assert started.wait(timeout=5)
    worker.close()
    release.set()
    worker.executor.shutdown(wait=True)
    assert scheduled.empty()
    assert not list(tmp_path.rglob('*.pdf'))
