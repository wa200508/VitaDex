# Local identification model

VitaDex currently uses Google's MediaPipe distribution of EfficientNet-Lite0, trained on ImageNet's 1,000 visual categories. It proposes broad categories from the starter catalog, not verified species identities or safety assessments.

- Upstream model: <https://storage.googleapis.com/mediapipe-models/image_classifier/efficientnet_lite0/float32/1/efficientnet_lite0.tflite>
- Distribution documentation: <https://ai.google.dev/edge/mediapipe/solutions/vision/image_classifier>
- SHA-256: `6c7ab0a6e5dcbf38a8c33b960996a55a3b4300b36a018c4545801de3a3c8bde0`
- Download size: approximately 18.6 MB. The binary is downloaded separately and excluded from Git; it must be present before building an offline APK.
- Input: center-cropped 224×224 RGB, float32, `(pixel - 127.5) / 127.5`.
- Output: 1,000 float32 softmax scores. `labels.json` was extracted from the model's embedded `labels_without_background.txt`; repeated ImageNet names such as “crane” are preserved in their original positions.
- Desktop runtime: LiteRT with two CPU threads. Android runtime: TensorFlow Lite 2.16.1 through a Java/PyJNIus bridge, also with two CPU threads. Android preprocessing uses Pillow and Python's float array, avoiding a NumPy runtime requirement there.

The global winning category must be supported by `data/nature_catalog.json`; an unsupported winner is never replaced by a lower-scoring nature category. The winner must exceed the next score by at least 0.15 and meet the 0.7 display threshold. These are initial gates, not calibrated reliability estimates. The user reviews a suggestion before saving, and the journal keeps the model source and score.

The daisy category deliberately maps to “Daisy-like flower” rather than a species: real-photo checks showed it also covers some sunflowers and dandelions. The model has limited coverage, domain bias, and potentially confident mistakes. Do not use its output to decide whether an organism is edible, harmless, medicinal, or safe to handle. Geographic and species-level validation and a specialist mobile nature model remain future work.

Download with `python download_identification_model.py`. This verifies the checksum before atomically installing the file, and the app verifies the model again before loading it. App runtime does not download models or upload photos. Upstream model weights and labels are third-party assets; review upstream distribution terms before redistribution in a release.
