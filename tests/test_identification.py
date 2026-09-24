import random

import pytest

from database import CARD_DB
from identification import (
    DEFAULT_SAFETY_MESSAGE,
    DemoIdentificationService,
    IdentificationCandidate,
    IdentificationResult,
    MINIMUM_CARD_CONFIDENCE,
)


def test_demo_service_returns_a_local_catalog_match_with_safety_guidance():
    service = DemoIdentificationService(CARD_DB, randomizer=random.Random(7))

    result = service.identify()

    assert result.source == 'demo'
    assert result.safety_message == DEFAULT_SAFETY_MESSAGE
    assert result.top_candidate is not None
    assert result.top_candidate.organism.name in CARD_DB.organisms
    assert result.top_candidate.confidence == 1.0
    assert result.has_confident_match


def test_low_confidence_candidate_is_available_to_the_scan_ui():
    organism = CARD_DB.get_organism('Glowleaf Beetle')
    assert organism is not None
    low_confidence_match = IdentificationCandidate(organism=organism, confidence=0.35)

    result = IdentificationResult(candidates=(low_confidence_match,), source='local-model')

    assert result.top_candidate == low_confidence_match
    assert result.top_candidate.confidence < 0.5
    assert not result.has_confident_match


def test_no_match_result_has_no_top_candidate():
    result = IdentificationResult(candidates=(), source='local-model')

    assert result.top_candidate is None
    assert not result.has_confident_match


def test_threshold_confidence_can_create_a_card():
    organism = CARD_DB.get_organism('Glowleaf Beetle')
    assert organism is not None

    result = IdentificationResult(
        candidates=(IdentificationCandidate(organism=organism, confidence=MINIMUM_CARD_CONFIDENCE),),
        source='local-model',
    )

    assert result.has_confident_match


@pytest.mark.parametrize('confidence', [-0.1, 1.1])
def test_candidate_confidence_must_be_a_probability(confidence):
    organism = CARD_DB.get_organism('Glowleaf Beetle')
    assert organism is not None

    with pytest.raises(ValueError, match='between 0 and 1'):
        IdentificationCandidate(organism=organism, confidence=confidence)
