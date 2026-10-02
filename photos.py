"""Private, bounded encounter photos without location metadata."""

import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PHOTO_PIXELS = 24_000_000
MAX_PHOTO_BYTES = 32 * 1024 * 1024


class PhotoError(ValueError):
    """A photo could not be safely decoded or stored."""


@dataclass(frozen=True)
class PhotoEncounter:
    photo_path: Path
    id: str
    observed_at: str


class PhotoStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def import_photo(self, source: Path) -> PhotoEncounter:
        ident = uuid4().hex
        target = self.directory / f'{ident}.jpg'
        try:
            if source.stat().st_size > MAX_PHOTO_BYTES:
                raise PhotoError('Please choose a photo smaller than 32 MB.')
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(source) as original:
                    if original.width * original.height > MAX_PHOTO_PIXELS:
                        raise PhotoError('Please choose a photo with at most 24 megapixels.')
                    image = ImageOps.exif_transpose(original).convert('RGB')
                    image.thumbnail((1600, 1600))
                    self.directory.mkdir(parents=True, exist_ok=True)
                    # A fresh image excludes EXIF/GPS and other source metadata.
                    clean = Image.new('RGB', image.size)
                    clean.paste(image)
                    clean.save(target, format='JPEG', quality=90)
        except (OSError, UnidentifiedImageError, Image.DecompressionBombWarning,
                Image.DecompressionBombError, PhotoError) as error:
            target.unlink(missing_ok=True)
            raise PhotoError(f'Could not use this photo: {error}') from error
        return PhotoEncounter(target, ident, datetime.now(timezone.utc).isoformat())

    def discard(self, encounter: PhotoEncounter) -> None:
        # Only remove owned photos, never the original picked file.
        if encounter.photo_path.parent == self.directory:
            encounter.photo_path.unlink(missing_ok=True)
