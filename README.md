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
2. Download the local photo-identification model: `python download_identification_model.py`
3. Launch the app: `python main.py`

Android is the first target platform; see [ANDROID.md](ANDROID.md) for building and device checks. The current model suggests broad categories from a small starter catalog and asks you to review them before saving. See [README_GAP_REPORT.md](README_GAP_REPORT.md) for implementation status against the product requirements above.

For development test APK downloads and Ubuntu emulator setup, see
[UBUNTU_EMULATOR.md](UBUNTU_EMULATOR.md). These snapshots are labeled VitaDex Test
and are separate from official releases.

ComfyUI artwork integration remains planned. The separate `download_models.py --workflow PATH` tool requires a supplied workflow; its missing default workflow is not needed to run the current photo flow. Private Hugging Face repositories require `HUGGINGFACEHUB_API_TOKEN`.

## License

The concept and descriptive content in this README are intended to support this project and are covered by the repository license. They are not intended for reuse, redistribution, or commercial exploitation without permission.

## Offline catalog direction

See [the architecture and delivery plan](docs/OFFLINE_CATALOG.md) for curated facts,
battery-friendly catalog updates, private cartoon artwork and print export.
Current nature entries are drafts. Safe catalog caching and single-card PDF export are implemented; hosted Android synchronization remains pending.

See [catalog operations](docs/CATALOG_OPERATIONS.md) and [printing](docs/PRINTING.md).
