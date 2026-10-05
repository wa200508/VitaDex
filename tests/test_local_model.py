import numpy as np
import pytest
from PIL import Image

from database import CARD_DB, NATURE_DB
from download_identification_model import MODEL_DIRECTORY, MODEL_FILENAME
from local_model import LocalIdentificationService, ModelError, prepare_image
from photos import PhotoEncounter


def encounter(tmp_path):
    path = tmp_path / 'photo.jpg'
    Image.new('RGB', (640, 480), 'green').save(path)
    return PhotoEncounter(path, 'encounter-id', '2026-10-01T00:00:00+00:00')


def predictor_with_scores(service, scores):
    values = np.zeros(1000, dtype=np.float32)
    for label, value in scores.items():
        values[service.labels.index(label)] = value
    return lambda pixels: values


def test_supported_high_score_suggests_real_category(tmp_path):
    service = LocalIdentificationService(NATURE_DB)
    service.predictor = predictor_with_scores(service, {'bee': 0.95, 'ladybug': 0.05})
    result = service.identify(encounter(tmp_path))
    assert result.has_confident_match
    assert result.top_candidate.organism.id == 'bee'
    assert not result.top_candidate.organism.is_demo
    assert result.source != 'demo'


def test_unsupported_winner_is_not_replaced_by_a_catalog_match(tmp_path):
    service = LocalIdentificationService(NATURE_DB)
    service.predictor = predictor_with_scores(service, {'Labrador retriever': 0.99, 'bee': 0.01})
    assert not service.identify(encounter(tmp_path)).candidates


def test_ambiguous_scores_have_no_match(tmp_path):
    service = LocalIdentificationService(NATURE_DB)
    service.predictor = predictor_with_scores(service, {'bee': 0.52, 'ladybug': 0.48})
    assert not service.identify(encounter(tmp_path)).candidates


def test_supported_low_score_does_not_qualify_for_a_card(tmp_path):
    service = LocalIdentificationService(NATURE_DB)
    service.predictor = predictor_with_scores(service, {'bee': 0.6, 'ladybug': 0.4})
    result = service.identify(encounter(tmp_path))
    assert result.top_candidate is not None
    assert not result.has_confident_match


@pytest.mark.parametrize('values', [np.full(1000, np.nan), np.ones(10), np.ones(1000), -np.ones(1000)])
def test_invalid_model_output_is_rejected(tmp_path, values):
    service = LocalIdentificationService(NATURE_DB, predictor=lambda pixels: values)
    with pytest.raises(ModelError, match='invalid category scores'):
        service.identify(encounter(tmp_path))


def test_demo_catalog_cannot_be_used_to_identify_photos():
    with pytest.raises(ModelError, match='Fictional'):
        LocalIdentificationService(CARD_DB)


def test_missing_model_has_actionable_error(tmp_path):
    (tmp_path / 'labels.json').write_bytes((MODEL_DIRECTORY / 'labels.json').read_bytes())
    service = LocalIdentificationService(NATURE_DB, model_directory=tmp_path)
    with pytest.raises(ModelError, match='download_identification_model.py'):
        service.identify(encounter(tmp_path))


def test_preprocessing_tensor_shape_range_and_colors(tmp_path):
    path = tmp_path / 'red.png'
    Image.new('RGB', (400, 200), (255, 0, 0)).save(path)
    pixels = prepare_image(path)
    assert len(pixels) == 224 * 224 * 3
    assert pixels.typecode == 'f'
    assert pixels.itemsize == 4
    assert pixels[:3].tolist() == [1, -1, -1]


@pytest.mark.skipif(not (MODEL_DIRECTORY / MODEL_FILENAME).is_file(), reason='download model first')
def test_real_local_model_handles_a_non_encounter(tmp_path):
    pytest.importorskip('ai_edge_litert')
    photo = tmp_path / 'blank.png'
    Image.new('RGB', (224, 224), 'black').save(photo)
    result = LocalIdentificationService(NATURE_DB).identify(PhotoEncounter(photo, 'blank', ''))
    assert not result.has_confident_match


@pytest.mark.skipif(not (MODEL_DIRECTORY / MODEL_FILENAME).is_file(), reason='download model first')
def test_checked_in_labels_match_the_pinned_models_embedded_order():
    import json
    import zipfile
    with zipfile.ZipFile(MODEL_DIRECTORY / MODEL_FILENAME) as model:
        embedded = model.read('labels_without_background.txt').decode().splitlines()
    assert json.loads((MODEL_DIRECTORY / 'labels.json').read_text()) == embedded


def test_new_catalog_taxa_do_not_break_an_older_model():
    from copy import deepcopy
    catalog = deepcopy(NATURE_DB)
    organism = next(iter(catalog.organisms.values()))
    known = organism.model_labels[0]
    organism.model_labels.append('future-model-only-organism')
    service = LocalIdentificationService(catalog)
    assert service.organisms_by_label[known] is organism
    assert 'future-model-only-organism' not in service.organisms_by_label
