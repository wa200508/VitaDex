"""Explicit single-flight catalog checks; never scheduled by scanning or startup."""
from concurrent.futures import ThreadPoolExecutor

from catalog_updates import CATALOG_MANIFEST_URL, update_catalog


class CatalogUpdateWorker:
    def __init__(self, cache, schedule, update=update_catalog):
        self.cache = cache
        self.schedule = schedule
        self.update = update
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='vitadex-catalog')
        self.busy = False
        self.closed = False

    def start(self, on_ready, on_error):
        if self.busy or self.closed:
            return False
        self.busy = True
        previous = self.cache.installed_release()

        def done(future):
            try:
                release, error = future.result(), None
            except Exception as exc:
                release, error = None, str(exc)
            if self.closed:
                return

            def deliver():
                self.busy = False
                if not self.closed:
                    if error is not None:
                        on_error(error)
                    else:
                        on_ready(release, release > previous)
            self.schedule(deliver)

        self.executor.submit(self.update, CATALOG_MANIFEST_URL, self.cache).add_done_callback(done)
        return True

    def close(self):
        # An already-started, bounded download may finish installing a valid snapshot.
        # It is used only on the next launch; there are no callbacks into a closed UI.
        self.closed = True
        self.executor.shutdown(wait=False, cancel_futures=True)
