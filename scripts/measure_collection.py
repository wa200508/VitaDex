"""Record desktop collection costs; these numbers are not phone energy claims."""
import argparse
import json
import platform
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import DEMO_DB
from journal import JournalRepository, JournalSession

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sizes', nargs='+', type=int, default=[10, 1000])
args = parser.parse_args()
records = []
with tempfile.TemporaryDirectory(prefix='vitadex-measure-') as directory:
    for size in args.sizes:
        statements = []
        class TracedRepository(JournalRepository):
            def _connect(self):
                db = super()._connect()
                db.set_trace_callback(statements.append)
                return db
        repo = TracedRepository(Path(directory) / f'{size}.sqlite3')
        organism = next(iter(DEMO_DB.organisms.values()))
        repo.save_cards(DEMO_DB.build_card(organism) for _ in range(size))
        session = JournalSession(repo)
        statements.clear()
        start = time.perf_counter()
        session.add_card(DEMO_DB.build_card(organism))
        elapsed = (time.perf_counter() - start) * 1000
        records.append({'existing_cards': size, 'append_ms': round(elapsed, 3),
            'card_writes': sum(sql.upper().startswith(('INSERT INTO CARDS', 'DELETE FROM CARDS',
                                                       'UPDATE CARDS')) for sql in statements)})
print(json.dumps({'platform': platform.platform(), 'python': platform.python_version(),
                  'scope': 'desktop SQLite append, not energy or UI frame timing', 'results': records}, indent=2))
