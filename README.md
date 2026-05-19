# VitaDex

VitaDex is a lightweight mobile-first application designed to organize and explore life system knowledge in a clean, accessible format. Built with Python and Kivy, the app provides an intuitive main page for presenting its purpose, with room to expand into more detailed data and discovery experiences.

## Features
- Simple, modern interface
- Python/Kivy-based mobile compatibility
- Easy to extend with additional content and navigation

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Launch the app: `python main.py`

## About
This repository contains the foundation for VitaDex, including the app entry point and dependency manifest. The main page can be updated with your application description and branding.

The concept and descriptive content in this README are intended to support this project and are covered by the repository license. They are not intended for reuse, redistribution, or commercial exploitation without explicit permission.

## Concept
VitaDex is designed as a pocket field guide for cataloging and exploring the living systems around you.

The app matches user scans with a nature catalog, then presents audio and visual descriptions to support discovery and safe interaction. Each encounter is captured as a custom collectible card and stored in an internal card book for review, export, and sharing.

VitaDex prioritizes child safety and accessibility: it will be free to use, require only the minimum permissions, include child-friendly controls, and avoid in-app purchases. The core experience is offline-first, with optional manual database updates so users can refresh local content while preserving device independence.

Scan processing will be optimized for local execution wherever possible, minimizing network overhead and preserving battery life. Optional audio capture may be offered as a disabled-by-default feature to provide contextual encounter data without compromising user control.