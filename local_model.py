"""Local TensorFlow Lite classification on desktop and Android."""

import json
import os
import math
import sys
from array import array
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageOps

from database import CardDatabase
from download_identification_model import MODEL_DIRECTORY, MODEL_FILENAME, verify_model
from identification import IdentificationCandidate, IdentificationResult
from photos import PhotoEncounter

MINIMUM_SCORE_MARGIN = 0.15
MODEL_SOURCE = 'efficientnet-lite0-imagenet-v1'


class ModelError(ValueError):
    """The local model is unavailable or returned an invalid result."""


def prepare_image(path: Path) -> array:
    resampling = getattr(Image, 'Resampling', Image)
    with Image.open(path) as source:
        image = ImageOps.fit(
            ImageOps.exif_transpose(source).convert('RGB'),
            (224, 224), method=resampling.BILINEAR,
        )
        pixels = array('f', ((value - 127.5) / 127.5 for value in image.tobytes()))
        return pixels


class DesktopInterpreter:
    def __init__(self, model_path: Path):
        try:
            from ai_edge_litert.interpreter import Interpreter
        except ImportError as error:
            raise ModelError('Install desktop dependencies from requirements.txt first.') from error
        self.interpreter = Interpreter(model_path=str(model_path), num_threads=2)
        self.interpreter.allocate_tensors()
        import numpy as np
        inputs = self.interpreter.get_input_details()[0]
        outputs = self.interpreter.get_output_details()[0]
        if (list(inputs['shape']) != [1, 224, 224, 3]
                or list(outputs['shape']) != [1, 1000]
                or inputs['dtype'] != np.float32 or outputs['dtype'] != np.float32):
            raise ModelError('The model has unsupported input or output tensors.')
        self.input_index = inputs['index']
        self.output_index = outputs['index']

    def __call__(self, pixels: array):
        import numpy as np
        tensor = np.frombuffer(pixels, dtype=np.float32).reshape((1, 224, 224, 3))
        self.interpreter.set_tensor(self.input_index, tensor)
        self.interpreter.invoke()
        return self.interpreter.get_tensor(self.output_index)[0]


class AndroidInterpreter:
    def __init__(self, model_path: Path):
        from jnius import autoclass
        self.model = autoclass('org.vitadex.LocalClassifier')(str(model_path))

    def __call__(self, pixels: array):
        if sys.byteorder != 'little':
            pixels.byteswap()
        return self.model.predict(pixels.tobytes())


class LocalIdentificationService:
    """Suggest supported nature categories; never reinterpret unsupported winners."""

    def __init__(self, catalog: CardDatabase, model_directory: Path = MODEL_DIRECTORY,
                 predictor: Optional[Callable] = None):
        self.catalog = catalog
        self.model_directory = Path(model_directory)
        self.predictor = predictor
        self.labels = json.loads((self.model_directory / 'labels.json').read_text(encoding='utf-8'))
        if len(self.labels) != 1000 or not all(isinstance(label, str) and label for label in self.labels):
            raise ModelError('The model labels must contain 1000 non-empty categories.')
        self.organisms_by_label = {}
        for organism in catalog.organisms.values():
            if organism.is_demo:
                raise ModelError('Fictional entries cannot be used for local identification.')
            for label in organism.model_labels:
                if self.labels.count(label) != 1 or label in self.organisms_by_label:
                    raise ModelError(f'Invalid or duplicate model label: {label}')
                self.organisms_by_label[label] = organism

    def identify(self, encounter: PhotoEncounter) -> IdentificationResult:
        try:
            if self.predictor is None:
                model_path = self.model_directory / MODEL_FILENAME
                if not verify_model(model_path):
                    raise ModelError(
                        'The local model is missing or damaged. Run '
                        'python download_identification_model.py before launching or building the app.'
                    )
                runtime = AndroidInterpreter if 'ANDROID_ARGUMENT' in os.environ else DesktopInterpreter
                self.predictor = runtime(model_path)
            scores = list(self.predictor(prepare_image(encounter.photo_path)))
            if (len(scores) != len(self.labels)
                    or not all(math.isfinite(value) and 0 <= value <= 1 for value in scores)
                    or not math.isclose(sum(scores), 1.0, abs_tol=0.01)):
                raise ModelError('The local model returned invalid category scores.')
            ranked = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
            winner = self.organisms_by_label.get(self.labels[int(ranked[0])])
            margin = float(scores[ranked[0]] - scores[ranked[1]])
            if winner is None or margin < MINIMUM_SCORE_MARGIN:
                return IdentificationResult(candidates=(), source=MODEL_SOURCE)
            return IdentificationResult(
                candidates=(IdentificationCandidate(winner, float(scores[ranked[0]])),),
                source=MODEL_SOURCE,
            )
        except ModelError:
            raise
        except Exception as error:
            raise ModelError(f'Local photo processing failed: {error}') from error
