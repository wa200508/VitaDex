# Implementation review against the README

The README remains the product specification. This review does not reduce its promises to fit the prototype.

## Current state

VitaDex has a Kivy interface, an extensible JSON catalog, locally generated card variations, and a versioned SQLite journal with legacy JSON migration. Runtime identification is a random demo; the catalog contains fictional organisms. There is no camera input, trained identification model, speech output, rendered organism artwork, or verified mobile build. Android is the first target platform; `buildozer.spec` now provides an initial demo build configuration (see `ANDROID.md`).

The current app uses local storage and makes no runtime network requests. It requests no camera, microphone, or location permissions, and includes no accounts, purchases, advertising, or analytics. These are useful foundations, but they do not establish that a future camera/model implementation meets the README's privacy and battery goals.

## Corrections made in this review

- Label the random sample flow as a demo and explicitly disclose its fictional catalog. Demo output no longer reports 100% identification confidence or qualifies as a confident match.
- Show observation safety guidance in the demo flow and card details, including successful card creation.
- Save a card before adding it to the visible collection or announcing success. Show failures to the user.
- Keep an unreadable journal unchanged and block additions for that session instead of silently replacing the collection with an empty one. Translate filesystem failures into journal errors as well as SQLite failures.
- Make home, demo, messages, previews, and card details scrollable; size description labels from their wrapped text. Adjust card-grid columns with width and stack collection controls so they fit narrow screens.
- Add an initial Android build configuration with an empty permission list and Android Back handling for popups and navigation. APK builds and physical-device tests remain outstanding.
- Provide visible Close/Home controls. Remove swipe-to-close behavior that would interfere with scrolling card details.

## Remaining work, in priority order

| Priority | README requirement | Evidence in the implementation | Required result |
| --- | --- | --- | --- |
| 1 | Match user scans with a nature catalog | `IdentificationService.identify()` accepts no encounter input. `VitaDexApp.build()` always installs `DemoIdentificationService`, which randomly chooses an entry. | Add an encounter input type, camera/photo acquisition, and a real local provider. Test distinct known inputs, unknown inputs, low-confidence results, and provider failures; never turn failed identification into a random match. |
| 1 | Help users safely discover real nature | `data/database.json` and `database.DEFAULT_DATABASE` contain Glowleaf Beetle, Streamfin Dart, and Sunflare Sprout, with invented facts and moves. | Build a reviewed real-organism catalog with stable identifiers, scientific names, factual descriptions, identification limits, and organism-specific safety information. Keep fictional samples explicitly separate from real encounters, including persisted cards. |
| 1 | Getting Started downloads required local ComfyUI models | `download_models.py` defaults to `card_generation/workflow_api.json`, which does not exist. No code invokes ComfyUI or loads downloaded checkpoints. The parser expects `nodes/type/args/checkpoint`, whereas ordinary ComfyUI API exports use node IDs with `class_type/inputs/ckpt_name`. Checkpoint filenames are not necessarily Hugging Face repository IDs. | Supply and test the intended workflow, explicit checkpoint-to-repository mappings, download destinations, and runtime integration. Clarify the division between identification models and card illustration models. Run the exact documented setup sequence on a fresh environment. |
| 2 | Present visual descriptions and custom collectible cards | `CardTile` displays `card.card_art` in a `Label`; catalog art assets are strings such as “Glowleaf Art 1”. Background style is not rendered; `templates/card/standard_background.svg` is unused. | Render real local images and the selected background, with a readable missing-image fallback. Generated illustrations must be labeled and must not stand in for evidence used to identify an organism. |
| 2 | Present audio descriptions | There is no playback or text-to-speech implementation. | Add user-initiated local speech or bundled narration with Stop controls and a text equivalent. Playback does not require microphone permission. If recording is later offered, keep it disabled by default as specified. |
| 2 | Child-friendly controls and minimum permissions | Generic safety guidance now appears, but there is no settings/parent-control flow or mobile permission lifecycle. | Define the controls, add a safe default configuration, request camera access only when the user chooses capture, and handle denial/revocation. Avoid adding location or microphone permissions without a concrete user-selected feature. |
| 2 | Mobile-first, accessible interface | Layouts now wrap and scroll, but dimensions are largely raw pixels. There is an initial Android demo build configuration, but no verified APK/device build, keyboard focus strategy, or assistive-technology validation. | Package and verify the Android target, use density-aware touch targets, and verify portrait/landscape, large text, keyboard navigation, contrast, and screen-reader behavior. A desktop window resized to phone dimensions is only an initial check. |
| 3 | Minimize network overhead and battery use | The demo is local; a real inference pipeline does not exist. Work in `perform_scan()` runs synchronously on the UI thread. | Run bounded inference outside the UI thread, prevent duplicate requests, release camera resources on pause, and measure latency, memory, battery, and offline operation on the target device. |
| 3 | Capture each encounter as a personal journal card | SQLite preserves card content, but `Card` has no encounter ID, timestamp, photo reference, provenance, or identification confidence. New-card badges are memory-only; sorting is a separate UI list. | Store encounter metadata with a versioned migration, distinguish demo/manual/model sources, and define whether ordering and unread status should persist. Keep existing card snapshots intact through migrations. |

## Validation

Regression tests cover demo confidence, unreadable journals, failed saves, successful durable additions, and filesystem errors, alongside the existing catalog, identification, download-parser, and migration tests. Run `python -m pytest`, `python -m ruff check .`, and compilation checks using the project's supported Python versions. Mobile-device and real-inference acceptance checks remain outstanding until those features exist.

This review passed 23 tests, Ruff checks, and Python compilation on Python 3.12. A Kivy smoke check under a virtual display at 320×568 exercised app construction, sample creation, SQLite persistence, card popups, and Back navigation. This does not validate TalkBack, a packaged APK, or physical Android device behavior.
