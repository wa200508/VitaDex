"""Export a pending human review packet, or prepare a separately reviewed catalog."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import CardDatabase
from editorial import apply_review, atomic_json, review_packet

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('action', choices=('export', 'apply'))
parser.add_argument('--catalog', type=Path, default=Path('data/database.json'))
parser.add_argument('--packet', type=Path, default=Path('data/editorial/ohio-review.json'))
parser.add_argument('--output', type=Path)
args = parser.parse_args()
catalog = json.loads(args.catalog.read_text())
CardDatabase.from_json(catalog)
if args.action == 'export':
    if args.packet.exists():
        parser.error('Packet exists; choose a new path to preserve review history.')
    atomic_json(args.packet, review_packet(catalog))
else:
    if args.output is None or args.output.resolve() == args.catalog.resolve():
        parser.error('Use a separate --output file; inspect it before publishing a catalog update.')
    reviewed = apply_review(catalog, json.loads(args.packet.read_text()))
    CardDatabase.from_json(reviewed)
    atomic_json(args.output, reviewed)
