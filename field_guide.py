"""Offline field-guide reading and source-constrained future discussion hooks.

No model, network, microphone or speech engine is initialized by this module.
"""

from dataclasses import dataclass
from typing import Protocol

from database import OrganismEntry

TOPICS = {
    'description': 'What is it?',
    'habitat': 'Where does it live?',
    'environment_role': 'How does it fit into its ecosystem?',
    'physical_dimensions': 'How big is it?',
    'notes': 'What else can I learn?',
}


@dataclass(frozen=True)
class Excerpt:
    id: str
    topic: str
    text: str
    sources: tuple[str, ...]


@dataclass(frozen=True)
class DiscussionRequest:
    organism_id: str
    revision: int
    question: str
    excerpts: tuple[Excerpt, ...]


class DiscussionProvider(Protocol):
    """Optional future local or explicitly connected provider.

    Select evidence IDs, never authoritative free-form facts. The app renders the
    stored excerpts itself. An empty selection means the catalog cannot answer.
    Implementations must support cancellation outside this synchronous boundary.
    """

    def select_evidence(self, request: DiscussionRequest) -> tuple[str, ...]: ...


class NarrationProvider(Protocol):
    """Future device speech adapter, controlled by an explicit listening action."""

    def speak(self, text: str) -> None: ...
    def stop(self) -> None: ...


def reviewed_excerpts(entry: OrganismEntry) -> tuple[Excerpt, ...]:
    # Publication validation is responsible for review authenticity and completeness.
    if entry.is_demo or entry.review_status != 'reviewed' or not entry.id:
        return ()
    excerpts = []
    for field in TOPICS:
        text = getattr(entry, field)
        sources = entry.fact_sources.get(field, [])
        if (text and isinstance(sources, list) and sources
                and all(isinstance(source, str) and source.startswith('https://')
                        and source in entry.references for source in sources)):
            excerpts.append(Excerpt(f'{entry.id}:{entry.revision}:{field}', field,
                                    text, tuple(sources)))
    return tuple(excerpts)


def prepare_discussion(entry: OrganismEntry, question: str) -> DiscussionRequest:
    question = question.strip()
    if not question or len(question) > 1000:
        raise ValueError('Ask a question between 1 and 1000 characters long.')
    excerpts = reviewed_excerpts(entry)
    if not excerpts:
        raise ValueError('Reviewed source material is not available for this organism yet.')
    # No photo, encounter location/time, or journal data crosses this boundary.
    return DiscussionRequest(entry.id, entry.revision, question, excerpts)


def render_evidence(request: DiscussionRequest, evidence_ids: tuple[str, ...]) -> str:
    """Reject invented/cross-organism IDs; only the trusted stored words are shown."""
    allowed = {excerpt.id: excerpt for excerpt in request.excerpts}
    if not isinstance(evidence_ids, tuple) or any(
            not isinstance(ident, str) or ident not in allowed for ident in evidence_ids):
        raise ValueError('The discussion provider returned unsupported evidence.')
    if not evidence_ids:
        return 'The reviewed guide does not have an answer to that question yet.'
    return '\n\n'.join(
        f'{allowed[ident].text}\nSources: ' + ', '.join(allowed[ident].sources)
        for ident in dict.fromkeys(evidence_ids)
    )


def introduction(entry: OrganismEntry) -> str:
    """Deterministic first reading for an encounter; also usable by future speech."""
    status = ('Fictional demo.' if entry.is_demo else
              'Catalog facts reviewed.' if entry.review_status == 'reviewed' else
              'Draft field guide; facts await scientific review.')
    return f'{entry.name}. {status}\n\n{entry.description}'


def read_topic(entry: OrganismEntry, topic: str) -> str:
    if topic not in TOPICS:
        raise ValueError('Unknown field-guide topic.')
    text = getattr(entry, topic) or 'This topic is not covered in the guide yet.'
    if entry.is_demo:
        return f'Fictional demo.\n\n{text}'
    evidence = next((item for item in reviewed_excerpts(entry) if item.topic == topic), None)
    if evidence:
        return f'{text}\n\nSources: ' + ', '.join(evidence.sources)
    return f'Draft field-guide text. Scientific review is pending.\n\n{text}'
