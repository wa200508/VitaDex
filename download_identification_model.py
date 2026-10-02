"""Install the pinned, public local image-classification model (no account required)."""

import argparse
import hashlib
import os
import tempfile
from pathlib import Path
from urllib.request import urlopen

MODEL_DIRECTORY = Path(__file__).parent / 'assets' / 'models'
MODEL_FILENAME = 'efficientnet_lite0.tflite'
MODEL_URL = (
    'https://storage.googleapis.com/mediapipe-models/image_classifier/'
    'efficientnet_lite0/float32/1/efficientnet_lite0.tflite'
)
MODEL_SHA256 = '6c7ab0a6e5dcbf38a8c33b960996a55a3b4300b36a018c4545801de3a3c8bde0'


def verify_model(path: Path) -> bool:
    if not path.is_file():
        return False
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest() == MODEL_SHA256


def download_model(directory: Path = MODEL_DIRECTORY) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / MODEL_FILENAME
    if verify_model(destination):
        return destination
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix='.part', delete=False) as target:
            temporary = Path(target.name)
            with urlopen(MODEL_URL, timeout=60) as response:
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        if not verify_model(temporary):
            raise ValueError('Model checksum did not match; the download was not installed.')
        temporary.replace(destination)
        return destination
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path, default=MODEL_DIRECTORY)
    args = parser.parse_args()
    try:
        installed = download_model(args.model_dir)
    except (OSError, ValueError) as error:
        raise SystemExit(f'Could not install the local model: {error}') from error
    print(f'Local identification model ready: {installed}')


if __name__ == '__main__':
    main()
