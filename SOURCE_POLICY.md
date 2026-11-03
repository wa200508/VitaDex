# Information pedigree

Every real-organism card must have claim-level citations and a recorded content
review. A source link alone does not establish that the source supports a claim.
Validation checks metadata and coverage; a human must check accuracy and record
an honest review. The Ohio starter catalog distinguishes AI source comparison
from independent human review. Fictional fixtures are never wildlife records.

## Editorial workflow

1. Identify the species using its scientific name. Prefer authoritative specialist
   sources: museums, government wildlife agencies, universities, and established
   taxonomic databases. Wikipedia is acceptable as a starting source; check the
   article's citations, warning banners, and actual support for each claim.
   Wikipedia is collaboratively edited, not universally peer reviewed or vetted.
2. Write a short original summary. Verify scientific name, common name, type, description, habitat, dimensions,
   ecological role, life stage, relationships, and any factual notes separately.
   Do not infer a claim just because it sounds plausible for the organism.
3. Record a reference for every factual field used, including publisher, title,
   HTTPS URL, access date, license/reuse terms, and required attribution. Do not
   copy unlicensed prose. Use a permanent revision URL for Wikipedia and a
   version/date for other changing sources where available. The main URL remains
   useful for finding subsequent corrections.
4. Resolve disagreements or omit the unsupported claim. Never use a general
   encyclopedia entry to justify handling, edibility, toxicity, or medical advice.
   Such advice requires separate specialist review and is outside this demo.
5. Record who reviewed the source-to-claim mapping and the review date. Only then
   set `content_kind` to `reviewed`. An automated import or model output must not
   self-assign reviewed status.
6. Recheck changed claims and references before releasing a new catalog. Saved
   cards preserve their original references and review information as snapshots;
   catalog changes do not silently rewrite provenance on existing cards.

## Data contract

Organisms carry `content_kind`: `fictional`, `unreviewed`, `source_checked`, or
`reviewed`. `source_checked` means the AI assistant consulted the sources and
compared the populated factual fields with them; it explicitly does not imply
independent human review. This status permits trying the cited starter cards in
the preview, with a visible human-review-pending notice. Only an actual recorded
human editorial review should promote an entry to `reviewed`. Automated imports
must not label themselves `reviewed` or skip evidence checks.
Missing provenance on a historical card is treated as unreviewed. Unreviewed
catalog entries cannot generate new cards. Fictional entries remain collectable
and explicitly disclose that their descriptions are invented.

A source-checked or reviewed entry requires `scientific_name`, `reviewed_by`, `reviewed_on`
(YYYY-MM-DD), and `sources`. Each source contains:

- `id`: unique within the organism, displayed beside supported card fields.
- `title`, `publisher`, `url`: a specific source and its HTTPS location.
- `revision_url`: optional permanent link, preferred when opening the reference.
- `accessed_on`: YYYY-MM-DD when the reviewer consulted the source.
- `supports`: factual field names supported by the source. All populated factual
  fields must be covered, including `habitat_type` if it is displayed on the card.
- `evidence`: optional brief source excerpt, its section/location, and a SHA-256
  checksum of that excerpt. The checksum detects accidental local edits; it does
  not prove accuracy, authenticity, or that the remote page is unchanged.
- `license` and `attribution`: the actual terms and credit needed for the content
  used, not a guessed license based on the publisher's name.

`rarity`, `move_set`, and the background are collectible game mechanics. They
must not imply conservation status, measured abundance, or factual abilities.
Illustrations are original stylized artwork, not diagnostic species photographs.

The card's Sources & Information section shows references, claim mappings,
review metadata, reuse information, and browser links. Source metadata stays in
the local journal with the card, including across JSON-to-SQLite migration.

## Remaining content work

- Complete independent human review of the source-checked Ohio starter entries.
  Do not attach real-species citations to fictional creatures to imply authority.
- Add a dedicated editorial/import workflow, source change monitoring, and review
  history rather than allowing unreviewed imports to become published facts.
- Define approved specialist sources for the regions and species being added.
- Add image-specific credits and licensing if external artwork is introduced.


## Ohio starter review record

See [OHIO_STARTER.md](OHIO_STARTER.md). Original card descriptions paraphrase facts;
brief attributed source excerpts provide inspectable evidence. Website text and
photos are not assumed freely reusable. These short excerpts do not establish a
license for full-page ingestion into a future RAG corpus; that requires separate
rights and content review. All current illustrations are original local vectors.


## Snapshot consistency and stable identity

Catalogs and saved snapshots share model field/type validation. Card Habitat,
Size, and Role, when stored, must match the organism snapshot whose references
are displayed. Invalid snapshots are rejected with a recoverable journal error;
no automatic source substitution repairs them. Stable organism IDs and declared
aliases identify discoveries separately from the original factual snapshot, so a
taxonomic rename does not require rewriting historical sources or announcing a
familiar species again.


See [EDITORIAL_REVIEW.md](EDITORIAL_REVIEW.md) for executable review packets and
explicit archived fact updates, and [CORPUS.md](CORPUS.md) for the distinction
between editorial retrieval passages and quoted third-party source text.
