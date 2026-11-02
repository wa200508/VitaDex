# VitaDex

A pocket field guide for cataloging and exploring the living systems around you.

## About VitaDex

VitaDex turns encounters with the living world into moments of understanding.
On a first discovery, it introduces the organism by name and tells its story
aloud. A collectible card preserves the encounter so the user can return, listen
again, explore cited information, and eventually ask deeper questions.

It is designed as a mobile companion that is curious, unobtrusive, and grounded in
trusted sources. Child safety and accessibility remain priorities: free to use,
minimal permissions, child-friendly controls, and no in-app purchases.

**Battery conservation is a core requirement.** Discovery should use deliberate,
short capture sessions, release sensors promptly, and avoid idle recognition,
background polling, unnecessary rendering, and repeated network or model work.
Microphone capture is disabled by default. Actual energy use must be measured on
phones; mobile battery efficiency has not yet been verified.

See [PRODUCT.md](PRODUCT.md) for the vision and [BATTERY_POLICY.md](BATTERY_POLICY.md)
for the power-use requirements.

## Current status

The destination is **Android/iPhone**, built with Python and Kivy. The current
computer preview lets you simulate discoveries with five real Ohio starter organisms; “Surprise me”
selects one at random. It does not use a camera or
identify real wildlife. Cards use bundled vector illustrations with habitat-inspired colors.

First discoveries request a spoken introduction and save a card. Repeat encounters
with the same species stay quiet and reuse the card, including after restarting.
You can replay introductions, search by name or habitat, filter by type, sort your card book,
and reopen the app to find
your locally saved collection. No account, model download, or network connection
is needed to run the demo after installing dependencies.

See [QUALITY_REVIEW.md](QUALITY_REVIEW.md) for the latest assessment,
[BACKLOG.md](BACKLOG.md) for prioritized work and acceptance criteria, and
[ROADMAP.md](ROADMAP.md) for the delivery sequence.

## Getting started

Use Python 3.11–3.13 on a desktop with a graphical display. From the repository:

```sh
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

Use the bottom navigation to switch between **Journal**, **Discover**, and
**Card book**. In Discover, choose **Discover this creature** for any creature. The saved
card opens with its illustration, description, habitat, size, role, moves, and notes.
Choose **Keep exploring** or **View card book**. Card book includes search, type
filtering, and sorting; **Mark all seen** clears new-card badges across restarts.
The Journal shows collection progress and your most recent card. Large collections
use 12-card pages; hidden or unchanged views are reused.

The journal is stored as `journal.sqlite3` in Kivy's platform-specific app data
directory (`VitaDexApp.user_data_dir`). A prior `journal.json` is migrated on first
use; the original JSON is retained. Back up the journal before manual recovery.
If storage cannot be read, the app reports the error and blocks additions for that
session. Resolve the storage problem and restart. If a save fails, the card is not
added or reported as saved. New-card badges are saved locally. Existing journals created before this feature
start with their older cards marked as seen.

Mobile installation, real identification, and source-grounded chat are not implemented. Always
observe real wildlife from a safe distance; never use this demo to decide whether
something is safe to touch or eat.

## Spoken discoveries

**Auto voice** starts on and can be turned off in Journal. The preference is saved.
Only the first discovery of each species requests automatic narration. Repeated
simulated encounters open the existing card without speaking or adding duplicates.
Future detections during an explicitly started discovery session use the same
flow and stay quiet without opening a popup for a known species. Continuous
background sensing is not part of the default design. Marking cards seen does not erase discovery history.

Every card has **Read aloud / replay introduction**, even when automatic voice is
off. **Stop reading** cancels playback; pause and shutdown cancel queued requests. Narration reads the saved name and description; it does not invent facts.
Fictional creatures are announced as fiction. Older unreviewed cards get a warning
instead of an unverified factual introduction.

Speech uses system voices, with no cloud speech API or microphone permission:

- Windows preview: Windows PowerShell and System.Speech.
- macOS preview: the built-in `say` tool.
- Linux preview: install `espeak-ng` or `espeak` through your OS package manager.
- Android/iOS: native TextToSpeech / AVSpeechSynthesizer bridges (Pyjnius /
  Pyobjus in the mobile build); mobile packaging and actual-device audio
  testing are still required. Native speech ownership/cancellation adapters are
  implemented, but have not been verified on actual phones.

Speech runs outside the rendering thread. If a system voice is unavailable, a
visible status explains the issue and the saved card remains readable. The UI
check injects a silent test speaker; passing it does not verify audible playback.

See [PRODUCT.md](PRODUCT.md) for the discovery-to-learning experience and planned
source-grounded conversation design.

## Sources and information pedigree

Each card exposes a **Sources & Information** section. Real-species content must
include citations supporting each populated factual field, a scientific name,
reviewer and review date, source access dates, and license/attribution details.
References remain attached to the saved card. Unreviewed entries cannot generate
new cards; historical cards with no source records display an unreviewed notice.
The starter collection includes **Dog, Cat, Red Maple, Kentucky Bluegrass, and
American Robin**, with short introductions, local illustrations, and references.
These entries are marked **source checked / human review pending**: the AI
assistant compared the facts with the linked sources, but no independent human
editor has signed them off. See [OHIO_STARTER.md](OHIO_STARTER.md) for the source
record and content decisions. Original fictional entries remain in
`data/demo_database.json` and test fixtures, rather than the default collection.

See [SOURCE_POLICY.md](SOURCE_POLICY.md) for the review workflow and data contract.
Wikipedia is an acceptable starting point, alongside specialist sources, but its
articles are not universally peer reviewed. Citation metadata is validated by the
app; source accuracy and claim support require an editorial review.

## Review, mobile preview, and future questions

The next-five implementation adds a [version-bound editorial workflow](EDITORIAL_REVIEW.md),
explicit archived fact updates in card details, an [offline editorial corpus](CORPUS.md),
and [Android build/device-test tooling](MOBILE_PREVIEW.md). Human sign-off and real
phone audio/energy measurements are still pending. No chat provider or generated
answer UI is connected yet.

## Development

```sh
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest
# Optional desktop storage measurements (not energy profiling)
python scripts/measure_collection.py
# Optional: exercises Kivy screens; requires a graphical display
python scripts/check_ui.py --screenshots /tmp/vitadex-preview
```

`download_models.py` is an optional experimental utility, not an app prerequisite.
There is no included ComfyUI workflow or model integration. Use `--workflow` only
if you have a compatible workflow and install `huggingface_hub` separately.
`jsonschema` supports catalog validation and the optional catalog sync script.

## License

The concept and descriptive content in this README are intended to support this project and are covered by the repository license. They are not intended for reuse, redistribution, or commercial exploitation without permission.
