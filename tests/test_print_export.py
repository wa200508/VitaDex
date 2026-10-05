from copy import deepcopy

from PIL import Image
from pypdf import PdfReader
import pytest

from database import NATURE_DB
from print_export import artwork_path, export_card


def card():
    return deepcopy(NATURE_DB.build_card(next(iter(NATURE_DB.organisms.values()))))


@pytest.mark.parametrize('paper,width,height', [('Letter', 612, 792), ('A4', 595.2756, 841.8898)])
def test_export_has_front_back_full_facts_and_sources(tmp_path, paper, width, height):
    sample = card()
    original = deepcopy(sample)
    result = export_card(sample, tmp_path, tmp_path / 'card.pdf', paper)
    reader = PdfReader(result.path)
    assert len(reader.pages) >= 3
    assert float(reader.pages[0].mediabox.width) == pytest.approx(width, abs=.01)
    assert float(reader.pages[0].mediabox.height) == pytest.approx(height, abs=.01)
    text = '\n'.join(page.extract_text() for page in reader.pages)
    assert sample.organism.description in text.replace('\n', ' ')
    assert sample.organism.references[0] in text.replace('\n', '')
    assert 'DRAFT FACTS / SUGGESTED ID' in text
    assert 'Trim 2.5 x 3.5' in text
    assert sample == original
    assert any('No local artwork' in warning for warning in result.warnings)
    fonts = reader.pages[0]['/Resources']['/Font'].get_object().values()
    assert any('/FontFile2' in font.get_object().get('/FontDescriptor', {}) for font in fonts)


def test_private_art_and_low_resolution_warning(tmp_path):
    sample = card()
    image = tmp_path / 'art.jpg'
    Image.new('RGB', (80, 80), 'green').save(image)
    sample.local_art_asset = 'art.jpg'
    result = export_card(sample, tmp_path, tmp_path / 'card.pdf')
    assert any('300 dpi' in warning for warning in result.warnings)
    sample.local_art_asset = '../outside.jpg'
    assert artwork_path(sample, tmp_path) is None


def test_failed_export_keeps_previous_file_and_cleans_temporary(tmp_path):
    sample = card()
    sample.organism.name = 'A very long scientific name ' * 100
    destination = tmp_path / 'card.pdf'
    destination.write_bytes(b'previous')
    with pytest.raises(ValueError, match='too long'):
        export_card(sample, tmp_path, destination)
    assert destination.read_bytes() == b'previous'
    assert not list(tmp_path.glob('*.tmp'))
