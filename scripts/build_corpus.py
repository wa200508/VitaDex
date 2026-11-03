"""Rebuild local editorial passages; does not fetch or license third-party text."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from corpus import build_corpus
from database import CardDatabase
from editorial import atomic_json
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--catalog', type=Path, default=Path('data/database.json'))
parser.add_argument('--output', type=Path, default=Path('data/corpus.json'))
args = parser.parse_args()
data = json.loads(args.catalog.read_text())
CardDatabase.from_json(data)
atomic_json(args.output, build_corpus(data))
