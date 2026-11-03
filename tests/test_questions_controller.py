from threading import Event

import pytest

from ask import AskError
from questions import QuestionController


class Provider:
    def __init__(self):
        self.key = "session-only"

    def clear(self):
        self.key = ""


def test_cancellation_releases_credentials_and_retains_single_worker():
    started, release = Event(), Event()

    def answer(card, question, provider, preview, cancelled):
        started.set()
        assert release.wait(2)
        return "ignored"

    callbacks, results = [], []
    controller = QuestionController(callbacks.append, answer)
    provider = Provider()
    job = controller.submit(None, "question", lambda *args: results.append(args), provider)
    assert started.wait(2)
    controller.cancel()
    assert not provider.key and job.cancelled.is_set()
    with pytest.raises(AskError, match="stopping"):
        controller.submit(None, "second", lambda *_: None)
    release.set()
    job.worker.join(2)
    assert not job.worker.is_alive()
    callbacks.pop()()
    assert results == []


def test_cancelled_queued_delivery_cannot_update_reopened_dialog():
    queued, results = [], []
    controller = QuestionController(queued.append, lambda *_: "answer")
    first = controller.submit(None, "first", lambda *args: results.append(args))
    first.worker.join(2)
    controller.cancel()
    second = controller.submit(None, "second", lambda *args: results.append(args))
    second.worker.join(2)
    for callback in queued:
        callback()
    assert results == [("answer", None)]


def test_failure_clears_key_and_shutdown_suppresses_delivery():
    queued, results = [], []

    def answer(*_):
        raise AskError("No supported evidence.")

    controller = QuestionController(queued.append, answer)
    provider = Provider()
    job = controller.submit(None, "question", lambda *args: results.append(args), provider)
    job.worker.join(2)
    assert not provider.key
    queued.pop()()
    assert results == [(None, "No supported evidence.")]
    job = controller.submit(None, "again", lambda *args: results.append(args))
    job.worker.join(2)
    controller.close()
    queued.pop()()
    assert len(results) == 1
    with pytest.raises(AskError, match="closed"):
        controller.submit(None, "after shutdown", lambda *_: None)
