"""Interfaces and local implementations for identifying nature encounters."""

import random
from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from database import CardDatabase, OrganismEntry


DEFAULT_SAFETY_MESSAGE = (
    'Observe from a safe distance. Do not touch, eat, or disturb living things; ask an adult for help.'
)
MINIMUM_CARD_CONFIDENCE = 0.7


@dataclass(frozen=True)
class IdentificationCandidate:
    """A possible organism match returned by an identification service."""

    organism: OrganismEntry
    confidence: float

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError('Candidate confidence must be between 0 and 1.')


@dataclass(frozen=True)
class IdentificationResult:
    """The result of identifying an encounter, including safety guidance."""

    candidates: Sequence[IdentificationCandidate]
    source: str
    safety_message: str = DEFAULT_SAFETY_MESSAGE

    @property
    def top_candidate(self) -> Optional[IdentificationCandidate]:
        return self.candidates[0] if self.candidates else None

    @property
    def has_confident_match(self) -> bool:
        candidate = self.top_candidate
        return candidate is not None and candidate.confidence >= MINIMUM_CARD_CONFIDENCE


class IdentificationService(Protocol):
    """A local or remote provider that returns possible organism matches."""

    def identify(self) -> IdentificationResult:
        """Identify an encounter and return zero or more ranked candidates."""


class DemoIdentificationService:
    """Temporary local provider used until camera/model identification is available."""

    def __init__(self, catalog: CardDatabase, randomizer: Optional[random.Random] = None):
        self.catalog = catalog
        self.randomizer = randomizer or random.Random()

    def identify(self) -> IdentificationResult:
        organisms = list(self.catalog.organisms.values())
        if not organisms:
            return IdentificationResult(candidates=(), source='demo')

        organism = self.randomizer.choice(organisms)
        return IdentificationResult(
            candidates=(IdentificationCandidate(organism=organism, confidence=1.0),),
            source='demo',
        )
