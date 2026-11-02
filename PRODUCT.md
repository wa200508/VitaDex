# VitaDex: discover, listen, keep learning

VitaDex turns encounters with the living world into moments of understanding.
On a first discovery, it introduces the organism by name and tells its story
aloud. A collectible card preserves that moment, inviting the user to return,
listen again, explore trusted information, and ask deeper questions.

The experience should feel like a knowledgeable companion: curious, clear,
unobtrusive, and grounded in sources the user can inspect. It should encourage
attention to the world around the user while preserving their phone's battery.

The product is a mobile app. Desktop runs are development previews. The central
loop is **discover → listen → keep → revisit → ask**.

## Battery conservation is a product requirement

VitaDex must use as little power as practical. The cost of sensing, identification,
speech, rendering, and network access must be considered together. The app should
be quiet and inactive when the user is not deliberately discovering or learning.

- Capture is deliberate and bounded. Camera and microphone stay off outside an
  explicitly started discovery session; microphone capture is off by default.
- Process the minimum useful input, then release sensors and inference resources.
  Do not run continuous recognition simply to decide whether something is new.
- Announce a species automatically only on its first discovery. Replay and
  source-grounded conversation happen when requested.
- Reuse saved cards, reviewed content, retrieval indexes, and appropriate cached
  results instead of repeating downloads, inference, or generation.
- Suspend discovery work when the app is backgrounded or the device locks. Do
  not keep the screen awake or acquire persistent wake locks for convenience.
- Measure energy use on real phones before claiming the app is battery efficient.
  Local execution and a low frame rate alone do not prove low total energy cost.

[BATTERY_POLICY.md](BATTERY_POLICY.md) defines implementation rules and release
checks. These are requirements to implement and verify, not a claim that the
current computer preview already meets a mobile battery budget.

## The central interaction

1. The user deliberately captures an encounter. Camera input, optional audio,
   or a simulated encounter supplies candidate matches.
2. Uncertain matches do not become discoveries. In a real identification build,
   show candidates and allow confirmation instead of asserting a guess as fact.
3. On the first confirmed discovery of a species, save its card and request its
   name and short introduction aloud. Show the same content in writing.
4. Further encounters with that species stay quiet by default. They do not add
   duplicate cards or open another unsolicited popup. A deliberate tap can open
   the existing card. Current deduplication is per species, not individual animal.
5. A user can browse cards and explicitly replay the introduction at any time.
   New/seen badges are independent of the permanent discovery history.
6. Later, the user can ask questions about the organism and receive answers based
   on reviewed sources, with citations and an optional spoken answer.

The current simulated-discovery implementation covers steps 1, 3, 4, and 5 using
a five-organism Ohio starter catalog. Its facts have been source checked by an
AI assistant; independent human review is pending. Encounter selection remains
manual/simulated: the app cannot identify real wildlife. The confidence threshold
is provisional and will need calibration for the chosen identification model.

## Spoken behavior

Introductions read the saved name and reviewed description, rather than invoking
an LLM to improvise facts. Fiction is introduced as fiction. Old unreviewed cards
announce that their facts have not been verified. Speech begins only after the
card is saved successfully. Speech failure leaves the card and written content
available, with explicit replay for retrying.

The voice switch controls automatic announcements. Replay is always deliberate.
Future mobile work must handle audio focus, silent mode, interruptions, voice
availability, headset routing, cancellation, and application lifecycle changes.
The initial native adapters are not a substitute for actual-device testing.
No passive background microphone or camera listening is implemented.

## Source-grounded conversation (planned)

The grounding unit is a real source passage, not a source title or URL.

- Ingest permitted text from reviewed references, with source identity, permanent
  revision/date, license, attribution, passage location, and a content hash.
- Keep original source text distinct from editorial card summaries, user notes,
  and fictional/game content. Use only the organism's reviewed corpus for factual
  retrieval; do not turn personal notes or fantasy moves into scientific evidence.
- Retrieve passages relevant to the selected organism and question. Preserve
  passage-to-reference mappings and pass that evidence to a provider adapter.
- Let users select their LLM/provider. Do not hardcode a model into the journal
  or put provider credentials in the repository or card data. Network-backed chat
  needs clear configuration and consent for whatever is sent to the provider.
- Treat retrieved text as evidence, not executable instructions. Ask the model to
  stay within the evidence, identify uncertainty, and cite supporting passages.
  Check citation identifiers against the retrieved set before displaying an answer.
- If evidence is missing or contradictory, say so and offer references rather
  than filling the gap with plausible biology. Avoid unsupported health, handling,
  or edibility claims. A citation does not guarantee a model interpreted it correctly.
- Separate the factual answer from optional narration. Show references even when
  an answer is spoken. Support browsing cards and replaying introductions offline
  when the chat provider is unavailable.

Chat, retrieval, provider configuration, and source-text ingestion are not yet
implemented. The present card provenance schema and saved snapshots are the
foundation for that work, not a functioning RAG system.


## Organism illustration direction

The target is realistic organisms with a restrained anime finish, natural anatomy,
and compositions that emphasize the traits discussed in the card's introduction.
A long neck, distinctive whiskers, or winged seeds should be deliberately visible,
not incidental or cropped out. Current placeholders are acceptable while the core
features are developed. See [ART_DIRECTION.md](ART_DIRECTION.md) for the visual
brief, review requirements, and battery-conscious asset delivery plan.
