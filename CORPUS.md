# Offline evidence corpus

`data/corpus.json` is a deliberately small, version-bound retrieval corpus for the
five Ohio starter organisms. It contains **original editorial summaries**, not
full reference pages and not primary-source passages. Each passage is labeled
`editorial_summary`, names its supported field and organism, and carries source
IDs/record hashes, entry/content hashes, attribution, review status, and a reuse
basis for the original wording. Third-party source records retain their own terms.

The original short source quotations remain separately identified as evidence in
`data/database.json`. No additional bulk source text, photos, or audio were copied.
Full primary-source passage ingestion remains gated on content and reuse review.
This is a usable small editorial corpus, not evidence for unlimited questions.

Rebuild explicitly when publishing a catalog change:

```sh
python scripts/build_corpus.py
```

`Corpus.bundled()` validates that the entire bundled corpus matches the current
catalog. Modified passages, changed sources/review state, and stale versions are
rejected. There is no network fetching or index-building loop when opening a card.

`Corpus.retrieve(species_id, question)` defaults to reviewed entries only.
Currently all starter entries await human review, so normal retrieval returns no
passages. Editorial preview tools/tests may explicitly use
`allow_source_checked=True`; that flag is not human approval and must not silently
become the production chat default. Results contain evidence only, never a
fabricated answer. `Corpus.references(passage)` resolves citations only for a
passage in that validated corpus.

Retrieval uses small lexical sets and a minimum query coverage rather than an
embedding model. It limits question/context size, scopes evidence to the selected
species, rejects selected handling/medical/edibility queries, and returns no
results when evidence does not match. These heuristics are not a comprehensive
safety filter or proof that a passage answers a question. Future chat must still
check support, citation IDs, uncertainty, prompt injection, and provider failures.

`data/corpus-evaluation.json` records five supported preview questions and several
unsupported ones, used by tests. Supported topics include dog helper roles, cat
whiskers, maple autumn leaves, grass spreading, and robin food. Lifespan prediction,
medical advice, edibility, and unrelated trivia are outside the current evidence.

Saved cards retain their own evidence: `snapshot_context(card, field)` uses the
saved organism and source snapshot, not the newest catalog under older citations.
It returns no factual context for fiction or unreviewed historical entries. A
future chat UI must decide explicitly whether to answer from the saved version or
ask the user to review an available catalog update.

VD-10 itself provides no provider or answer UI. The first VD-11 interface now
uses this foundation; see [ASK_VITADEX.md](ASK_VITADEX.md). It selects/assembles
evidence rather than displaying arbitrary generated prose. Persistent key storage
and broader conversation are not implemented.
