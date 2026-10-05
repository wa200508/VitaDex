"""Private, bounded encounter photos without location metadata."""

import warnings
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

MAX_PHOTO_PIXELS = 24_000_000
MAX_PHOTO_BYTES = 32 * 1024 * 1024


class PhotoError(ValueError):
    """A photo could not be safely decoded or stored."""


@dataclass(frozen=True)
class PhotoEncounter:
    photo_path: Path
    id: str
    observed_at: str
    art_path: Path | None = None


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

    def create_art(self, encounter: PhotoEncounter) -> PhotoEncounter:
        """Make a bounded local illustration after identification, preserving the photo."""
        if encounter.photo_path.parent != self.directory:
            raise PhotoError('Artwork requires a private encounter photo.')
        target = encounter.photo_path.with_name(encounter.photo_path.stem + '-art.jpg')
        try:
            with Image.open(encounter.photo_path) as original:
                image = original.convert('RGB')
                image.thumbnail((768, 768))
                # A small median filter and reduced palette need no model or network.
                image = ImageOps.posterize(image.filter(ImageFilter.MedianFilter(3)), 4)
                image.save(target, format='JPEG', quality=90)
        except OSError as error:
            target.unlink(missing_ok=True)
            raise PhotoError(f'Could not create artwork: {error}') from error
        return replace(encounter, art_path=target)

    def discard(self, encounter: PhotoEncounter) -> None:
        # Only remove owned photos, never the original picked file.
        if encounter.photo_path.parent == self.directory:
            encounter.photo_path.unlink(missing_ok=True)
        if encounter.art_path is not None and encounter.art_path.parent == self.directory:
            encounter.art_path.unlink(missing_ok=True)
