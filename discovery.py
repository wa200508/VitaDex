"""The discovery loop shared by simulated and future camera/audio encounters."""
from dataclasses import dataclass
from threading import RLock
from identity import organism_key
from typing import Optional

from database import Card, CardDatabase
from identification import IdentificationResult
from journal import JournalSession
from provenance import validate_provenance
from dataclasses import asdict



def introduction(card: Card) -> str:
    """Read the saved description, never generate or embellish biological facts."""
    organism = card.organism
    validate_provenance(asdict(organism))
    if organism.content_kind == 'unreviewed':
        return f'{organism.name}. This card has not been source reviewed. Its facts are not verified.'
    prefix = 'Fictional demo creature. ' if organism.content_kind == 'fictional' else ''
    return f'{organism.name}. {prefix}{organism.description}'


@dataclass(frozen=True)
class Discovery:
    card: Card
    is_first: bool

    @property
    def narration(self) -> str:
        return introduction(self.card)


class DiscoveryService:
    def __init__(self, catalog: CardDatabase, journal: JournalSession):
        self.catalog, self.journal = catalog, journal
        self.lock = RLock()

    def encounter(self, result: IdentificationResult) -> Optional[Discovery]:
        # A future sensor must pass the same confidence and content checks as the demo.
        if not result.has_confident_match:
            return None
        with self.lock:
            return self._encounter(result.top_candidate.organism)

    def _encounter(self, organism):
        key = organism_key(organism)
        card = self.journal.by_key.get(key) or self.journal.legacy_names.get(organism.name.strip().casefold())
        if card is not None:
            return Discovery(card, is_first=False)
        card = self.catalog.build_card(organism)
        # Saving is the boundary: failed writes must not announce a new discovery.
        saved, first = self.journal.discover_card(card)
        return Discovery(saved, is_first=first)
