# VitaDex: curated knowledge, private encounters

Status: hosting architecture plus local artwork, validated offline catalog caching, publication/update commands, and single-card PDF export. No server is provisioned and no background synchronization runs in the app yet. See CATALOG_OPERATIONS.md and PRINTING.md for current usage.

## Product boundary

A card consists of an approved catalog entry, an encounter record, and optional personal
artwork. Recognizing an organism selects an existing entry; it never generates facts.
Art is decorative and may be replaced locally without changing identity or knowledge.
All domains of life belong in the catalog: bacteria, archaea, and eukaryotes, including
plants, fungi and animals. User-facing wording uses “organism”, “living thing”, and
“encounter”. Taxonomic ranks are data, not an animal-specific class hierarchy.

The current ImageNet model only recognizes a small supported subset and does not have a
giraffe label. Its category suggestions are not verified species identifications.
Keep uncertain observations separate from verified collection membership. A future
recognizer must be evaluated on supported taxa, confusing lookalikes and unknown inputs;
select the narrowest supported taxon, never infer a species from a genus-level result.
Artwork processing does not repeat recognition. Microbial identification may require
microscopy or expert evidence beyond an ordinary phone photograph.

## Hosting decision

Use managed PostgreSQL for the editorial source of truth, with a small authenticated
editorial service. Clients do not connect to PostgreSQL. Publish immutable catalog JSON
bundles to HTTPS object storage behind a CDN. This keeps reads inexpensive, cacheable,
and independent of the editorial service being available. Start with reviewed JSON in
Git and a publication validator; introduce the database/editor UI when multiple curators
need it. Choose a hosting vendor after region, budget and curator access are known.

Editorial tables: taxa (stable internal ID), taxon_names, taxonomic_identifiers
(source, identifier, release), entry_revisions, facts, sources, fact_sources, reviews,
and catalog_releases. Store sources with title, authors, publication date, DOI or stable
URL, relevant page/section, retrieval date, and license. Store fact statements separately
from display layout. Reviews name the reviewer, date, exact revision and decision.
Publication requires a second-person review; corrections create new revisions.

Use internal IDs across name changes. External taxonomy identifiers must include the
source and release; they are not universally permanent. Taxonomic splits/merges require
an explicit mapping and possibly re-identification, not silent collection rewrites.
Darwin Core terms inform interchange. Taxonomy authorities establish identity; they do
not automatically substantiate ecology, size or safety statements.

## Scientific publication policy

Each displayed factual field needs supporting sources at the same taxonomic scope.
Prefer peer-reviewed research, authoritative syntheses and maintained institutional
references. Record uncertainty, geographic scope and exceptions. One paper is not proof
of consensus: a curator checks relevance, conflicting evidence and current acceptance.
Wikipedia links alone are discovery aids, not completed scientific review.

Bundled entries currently remain drafts. `review_status`, `revision`, and `fact_sources`
record this distinction; adding citations is not itself scientific validation. The
publication gate checks complete attribution and review metadata before a non-demo entry
can be published. Fictional samples never enter the scientific release channel.
Do not invent reviewers or silently promote old entries. Retractions/corrections revoke
or supersede revisions; retained encounters display a correction notice after syncing.

## Offline operation and battery budget

Ship a baseline catalog. Startup, browsing, scanning, saving, editing artwork and printing
read local files/SQLite only. No connection check, DNS lookup or server request is needed.
Keep the currently active immutable catalog plus the previous known-good release.

Later implement Android WorkManager unique periodic work (roughly daily, with a broad
flex window), requiring an unmetered connection, charging and battery-not-low. The OS
may defer it indefinitely; offline use must still work. Do not use a Python timer or poll
connectivity. Background updates are optional and pauseable. A visible “Check for catalog
updates” action may run on mobile data only when the user explicitly chooses it.

A small manifest carries schema version, monotonic release number, bundle size, SHA-256,
publication date, minimum app version and immutable bundle URL. Use conditional HTTP
requests, bounded timeouts, a size cap, exponential retry and no more than one worker.
Download to a temporary file, validate digest, schema, IDs, citations and review records,
then atomically switch the active pointer. Interruptions, invalid data, insufficient
space or an incompatible schema leave the old catalog usable. TLS authenticates the
endpoint; a digest only detects corruption. Add signed manifests and key rotation before
supporting mirrors or untrusted distribution. Prevent rollback to an older release.

Keep model downloads separate: they are much larger and require explicit consent.
New catalog model labels must not break an older installed recognizer; unsupported taxa
can be browsed but cannot be awarded from unsupported recognition results.

## Private collection and artwork

The journal keeps the taxon ID and exact fact revision/snapshot used at capture, encounter
time, model/source and uncertainty, plus private image references. Catalog updates never
overwrite personal art or silently alter historical identification. Offer an explicit
fact refresh with revision history when the catalog changes.

Current implementation makes a maximum 768-pixel median-filtered, posterized derivative
on the existing scan worker after an accepted model suggestion. It uses Pillow already
in the APK, no additional model or service. The original private photo remains unchanged
and metadata-stripped. The review screen lets the user choose original or cartoon art;
both cancellation and errors clean up owned files. Existing journal entries still load.
This style is a first lightweight approximation, to be evaluated on real device photos.

Personal photos, location and collection contents never upload for catalog updates.
Account backup/multi-device sync is a separate opt-in project with encryption, deletion,
conflict rules and explicit consent; it is not needed for catalog distribution.

## Print export design (single-card baseline implemented; remaining options planned)

Add “Export for printing” to card detail and collection selection. Generate an offline
PDF from the stored fact revision and selected local artwork. Offer a single-card
front/back PDF and Letter/A4 sheets with crop marks. Default trim is 2.5 by 3.5 inches,
with optional 0.125-inch bleed and a safe text inset. Embed fonts, retain vector text,
check image resolution against 300 dpi, and preserve aspect ratio. A print-provider
preset must control sheet size, bleed, duplex alignment and color requirements; do not
claim a universal commercial-print specification or automatic CMYK compatibility.

Show an on-screen preview and warn about low-resolution art. Include scientific name,
review status, fact revision and a compact source key; append readable full references.
Draft/suggested cards and fictional demos retain those labels in exported files.
Scientific sources and artwork must have recorded redistribution rights where applicable.
Use Android ACTION_CREATE_DOCUMENT to save/share the PDF through the system picker,
without broad storage permission. Never send a child's photo to a printer automatically.
Test trim/bleed dimensions, font embedding, long names and citations, multiple scripts,
page overflow, duplex orientation, offline operation and real printed samples.

## Delivery order and acceptance

1. This change: architecture, explicit draft metadata, publication guard, local art and
   original-photo choice, journal compatibility and broad organism wording.
2. Curate a small scientifically reviewed catalog; implement safe cached catalog loading
   and publication CI. Test interrupted updates and rejected revisions before hosting.
3. Host the manifest/bundles; integrate constrained WorkManager updates and manual checks.
   Measure network requests and battery usage with airplane-mode and charging tests.
4. Implement PDF export/system save flow and visually verify print proofs.
5. Upgrade/evaluate recognition coverage, then test the full collection flow on devices.

Scientific review, hosted sync, broad recognition, multi-card printing and on-device validation remain outstanding. Single-card PDFs have desktop tests and rendered proof inspection.

## Primary references

- Android WorkManager constraints and periodic work:
  https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work
- Android document creation without broad storage access:
  https://developer.android.com/training/data-storage/shared/documents-files
- Darwin Core taxonomy vocabulary: https://dwc.tdwg.org/terms/
- GBIF taxonomy release migration context:
  https://data-blog.gbif.org/post/catalogue-of-life-taxonomic-backbone/

## Pokédex-style encounters and optional discussion

The intended experience is capture → identify → open the organism's introduction →
explore questions. The first reading is deterministic catalog text, not generated text.
The field-guide UI now exposes local topic questions and shows sources when a topic has
reviewed attribution. Draft content remains visibly labeled. It works in airplane mode.

Automatic recording is the target for adequately evaluated recognition. Until that
quality milestone, the current flow opens the suggested entry automatically but retains
explicit Save/Discard. A future automatic encounter log should distinguish suggestions
from verified collection entries, deduplicate repeat camera detections, offer undo, and
stop when the camera closes. It must not repeatedly photograph or infer in the background.

`field_guide.py` introduces optional provider contracts without adding an AI dependency:

- `NarrationProvider`: speak a supplied catalog script and stop. Device TTS is sufficient;
  an LLM is unnecessary for reading a description. Add a Listen/Stop control, stop on
  pause/navigation, and respect audio settings before enabling narration. No microphone
  is needed to read aloud. Speech input would be a separate opt-in capability.
- `DiscussionProvider`: accept a question, organism ID, revision and reviewed excerpts;
  return evidence IDs. `render_evidence` rejects unknown IDs and renders exact catalog
  wording with sources. Empty evidence yields an explicit no-answer response. This is
  deliberately extractive: valid citations alone would not prove generated prose true.

The initial retrieval scope is one organism revision and a few short factual fields;
no vector database or embedding model is needed. Expand to locally indexed, reviewed
passages only when the corpus warrants it. Current draft entries cannot prepare an AI
request. Publication review must remain authoritative; these types do not authenticate
an arbitrary caller's claim that a record is reviewed.

A future adapter may use a small device model or an explicitly connected chatbot
service. Neither adapter is implemented or selected. Benchmark RAM, APK/model size,
latency, heat and battery on target phones before choosing a native model; download it
only on request. A cloud adapter needs explicit consent and a supported authenticated
integration; an installed chatbot app does not imply access to its session or API.
Send only the question and minimum source passages, never the encounter photo, location
or entire journal by default. Treat questions and source documents as untrusted text;
providers get no tools or authority to edit facts or collection membership.

Evidence selection can still be irrelevant or incomplete even when every displayed word
is sourced. Evaluate question relevance, abstention, taxonomic scope and adversarial
requests before exposing free-text discussion. More conversational generated wording
requires additional grounding evaluation and may never meet a strict “only the script”
contract. Keep extractive reading available as the reliable fallback.

AI integration remains last priority, after curated content, safe offline updates,
print export and recognition/device validation. No network calls, provider SDKs, model
loads, voice recording or automatic speech were added by this foundation.

## Collection and audio implementation update

Saved-card artwork replacement, deliberate deletion and aged orphan cleanup are now implemented. Android Listen/Stop uses the platform TTS engine with an installed offline English voice; no language model is involved. See COLLECTION_AND_AUDIO.md for usage and remaining device checks.
