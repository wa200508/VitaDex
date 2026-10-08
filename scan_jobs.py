"""One local scan at a time, with cancellation before publishing a result."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4


class ScanWorker:
    def __init__(self, photo_store, service, schedule):
        self.photo_store = photo_store
        self.service = service
        self.schedule = schedule
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='vitadex-scan')
        self.future = None
        self.generation = 0
        self.closed = False

    @property
    def busy(self):
        return self.future is not None

    def start(self, source, on_result, on_error, on_cancelled):
        if self.busy or self.closed:
            return False
        self.generation += 1
        generation = self.generation

        def process():
            encounter = None
            temporary = None
            try:
                if str(source).startswith('content://'):
                    from jnius import autoclass
                    self.photo_store.directory.mkdir(parents=True, exist_ok=True)
                    temporary = self.photo_store.directory / f'picker-{uuid4().hex}.tmp'
                    activity = autoclass('org.kivy.android.PythonActivity').mActivity
                    autoclass('org.vitadex.PhotoIO').copyUri(activity, str(source), str(temporary))
                    path = temporary
                else:
                    path = Path(source)
                encounter = self.photo_store.import_photo(path)
                encounter, result = self.process_encounter(encounter)
                return encounter, result, None
            except Exception as error:
                return encounter, None, error
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)

        self.future = self.executor.submit(process)

        def completed(future):
            encounter, result, error = future.result()
            if self.closed:
                if encounter is not None:
                    self.photo_store.discard(encounter)
                return

            def deliver():
                self.future = None
                if generation != self.generation:
                    if encounter is not None:
                        self.photo_store.discard(encounter)
                    on_cancelled()
                elif error is not None:
                    if encounter is not None:
                        self.photo_store.discard(encounter)
                    on_error(error)
                else:
                    on_result(encounter, result)

            self.schedule(deliver)

        self.future.add_done_callback(completed)
        return True

    def process_encounter(self, encounter):
        result = self.service.identify(encounter)
        if result.has_confident_match:
            encounter = self.photo_store.create_art(encounter)
        return encounter, result

    def cancel(self):
        self.generation += 1

    def close(self):
        self.closed = True
        self.cancel()
        # Already-running bounded inference may finish; its result is discarded.
        self.executor.shutdown(wait=False)


class ArtworkWorker(ScanWorker):
    """Reuse bounded import/cancellation, without running identification again."""

    def __init__(self, photo_store, schedule):
        super().__init__(photo_store, None, schedule)

    def process_encounter(self, encounter):
        return self.photo_store.create_art(encounter), None
