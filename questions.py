"""UI-independent ownership of a single cancellable question request."""

from dataclasses import dataclass, field
from threading import Event, Lock, Thread

from ask import answer_card, AskError


@dataclass
class QuestionJob:
    generation: int
    provider: object
    cancelled: Event = field(default_factory=Event)
    worker: object = None


class QuestionController:
    def __init__(self, dispatch, answer=answer_card):
        self.dispatch, self.answer = dispatch, answer
        self.lock = Lock()
        self.active = None
        self.generation = 0
        self.closed = False

    def submit(self, card, question, callback, provider=None, allow_source_checked=False):
        with self.lock:
            if self.closed:
                raise AskError("Questions are closed.")
            if self.active is not None:
                raise AskError("The previous request is still stopping. Try again shortly.")
            self.generation += 1
            job = QuestionJob(self.generation, provider)
            self.active = job

        def work():
            try:
                value = self.answer(card, question, provider, allow_source_checked, job.cancelled)
                error = None
            except Exception as caught:
                value, error = None, str(caught)
            finally:
                if provider:
                    provider.clear()
                with self.lock:
                    if self.active is job:
                        self.active = None

            def deliver():
                with self.lock:
                    valid = (
                        not self.closed
                        and not job.cancelled.is_set()
                        and self.generation == job.generation
                    )
                if valid:
                    callback(value, error)

            self.dispatch(deliver)

        job.worker = Thread(target=work, daemon=True)
        job.worker.start()
        return job

    def cancel(self):
        with self.lock:
            self.generation += 1
            job = self.active
            if job:
                job.cancelled.set()
        if job and job.provider:
            job.provider.clear()

    def close(self):
        with self.lock:
            self.closed = True
        self.cancel()
