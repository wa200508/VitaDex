"""One print export at a time; PDF generation and document I/O stay off the UI thread."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from uuid import uuid4


class ExportWorker:
    def __init__(self, root, schedule):
        self.root = Path(root)
        self.schedule = schedule
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='vitadex-print')
        self.busy = False
        self.closed = False

    def start(self, card, paper, on_ready, on_error):
        if self.busy or self.closed:
            return False
        self.busy = True
        snapshot = deepcopy(card)
        destination = self.root / 'exports' / f'vitadex-{uuid4().hex}.pdf'

        def generate():
            from print_export import export_card
            return export_card(snapshot, self.root, destination, paper)

        def done(future):
            try:
                result, error = future.result(), None
            except Exception as exc:
                result, error = None, str(exc)
            if self.closed:
                destination.unlink(missing_ok=True)
                return

            def deliver():
                self.busy = False
                if self.closed:
                    destination.unlink(missing_ok=True)
                elif error is not None:
                    on_error(error)
                else:
                    on_ready(result)
            self.schedule(deliver)

        self.executor.submit(generate).add_done_callback(done)
        return True

    def close(self):
        self.closed = True
        self.executor.shutdown(wait=False)
