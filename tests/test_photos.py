from pathlib import Path

import pytest
from PIL import Image

from photos import PhotoError, PhotoStore


def test_import_keeps_a_bounded_private_copy_without_metadata(tmp_path):
    original = tmp_path / 'original.jpg'
    metadata = Image.Exif()
    metadata[270] = 'Sensitive source metadata'
    Image.new('RGB', (2000, 1200), 'blue').save(original, exif=metadata)
    original_bytes = original.read_bytes()
    store = PhotoStore(tmp_path / 'photos')

    encounter = store.import_photo(original)

    with Image.open(encounter.photo_path) as saved:
        assert saved.size == (1600, 960)
        assert not saved.getexif()
        assert saved.mode == 'RGB'
    assert encounter.id in encounter.photo_path.name
    assert encounter.observed_at.endswith('+00:00')
    store.discard(encounter)
    assert not encounter.photo_path.exists()
    assert original.read_bytes() == original_bytes


def test_exif_orientation_is_applied_before_metadata_is_removed(tmp_path):
    original = tmp_path / 'rotated.jpg'
    metadata = Image.Exif()
    metadata[274] = 6
    Image.new('RGB', (80, 40), 'red').save(original, exif=metadata)
    encounter = PhotoStore(tmp_path / 'photos').import_photo(original)
    with Image.open(encounter.photo_path) as saved:
        assert saved.size == (40, 80)
        assert not saved.getexif()


def test_invalid_photo_does_not_leave_a_saved_file(tmp_path):
    original = tmp_path / 'not-a-photo.jpg'
    original.write_text('invalid')
    store = PhotoStore(tmp_path / 'photos')
    with pytest.raises(PhotoError):
        store.import_photo(original)
    assert not list(store.directory.glob('*.jpg'))


def test_photo_size_limit_is_enforced_before_decoding(tmp_path, monkeypatch):
    monkeypatch.setattr('photos.MAX_PHOTO_BYTES', 3)
    original = tmp_path / 'large.jpg'
    original.write_bytes(b'1234')
    with pytest.raises(PhotoError, match='smaller than'):
        PhotoStore(tmp_path / 'photos').import_photo(original)


def test_pixel_limit_is_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr('photos.MAX_PHOTO_PIXELS', 10)
    original = tmp_path / 'large.png'
    Image.new('RGB', (20, 20)).save(original)
    with pytest.raises(PhotoError, match='megapixels'):
        PhotoStore(tmp_path / 'photos').import_photo(original)


def test_discard_never_deletes_an_unowned_source(tmp_path):
    from photos import PhotoEncounter
    original = tmp_path / 'original.jpg'
    original.write_bytes(b'original')
    store = PhotoStore(tmp_path / 'photos')
    store.discard(PhotoEncounter(Path(original), 'id', ''))
    assert original.exists()
