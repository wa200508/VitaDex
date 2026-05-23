# VitaDex

A pocket field guide for cataloging and exploring the living systems around you.

## About VitaDex

VitaDex is a mobile-first application designed to help users discover, identify, and safely interact with nature. The app matches user scans with a nature catalog, then presents audio and visual descriptions to support discovery and safe interaction. Each encounter is captured as a custom collectible card, creating a personal nature journal.

VitaDex prioritizes child safety and accessibility: it will be free to use, require only the minimum permissions, include child-friendly controls, and avoid in-app purchases. The core experience is designed for learners of all ages.

Scan processing will be optimized for local execution wherever possible, minimizing network overhead and preserving battery life. Optional audio capture may be offered as a disabled-by-default feature.

## Features

- Clean, accessible interface built with Python and Kivy
- Local-first scan processing to minimize network usage
- Custom collectible card journal to track discoveries
- Child-safe and permission-conscious design
- Easy to extend with additional content and navigation

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Download required local models for ComfyUI: `python download_models.py`
   - If you use private Hugging Face models, set `HUGGINGFACEHUB_API_TOKEN` first.
3. Launch the app: `python main.py`

## License

The concept and descriptive content in this README are intended to support this project and are covered by the repository license. They are not intended for reuse, redistribution, or commercial exploitation without permission.
