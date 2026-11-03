# Human editorial review and fact updates

The pending packet is `data/editorial/ohio-review.json`. It records each exact
entry version, populated factual field and its supporting sources, references,
checks, and blank reviewer/decision fields. No human review has been fabricated.

1. Inspect facts and the actual linked sources; verify scientific names, wording
   for young readers, field support, quotation/reuse terms, and attribution.
2. In a copy of the packet, a human reviewer declares their name, date,
   `reviewer_kind: "human"`, completed checks, notes, and either `approved` or
   `changes_requested`. Leave unreviewed entries `pending`.
3. Prepare a separate proposed catalog:

```sh
python scripts/review_catalog.py apply --packet /path/to/completed-review.json --output /tmp/reviewed-catalog.json
```

The tool refuses changed entry/source versions, altered claim/reference mappings,
duplicate/unknown entries, incomplete checks, unnamed/nonhuman declarations, and
future review dates. `pending` does not change status; `changes_requested` returns
the entry to unreviewed. Identity is **declared**, not cryptographically verified:
repository review/access controls remain necessary before publishing approvals.
Never have an automated importer or model impersonate the human reviewer.

Inspect and version-control the proposed catalog and completed packet before
publishing it; regenerate the corpus for that catalog. Existing saved cards do
not silently change. Export a new packet for future content revisions:

```sh
python scripts/review_catalog.py export --packet /tmp/next-review.json
```

Export refuses to overwrite an existing packet. The entry hash excludes approval
labels/date so an editorial decision can be attached, but includes factual text,
identity, source records, and excerpt evidence. Changing those requires a new
review. Historical packets remain inspectable in version control.

## Updating an existing saved card

When the bundled catalog differs from a saved organism snapshot, card details
show **Review available fact update**. The preview lists changed fields, the new
introduction, status, and references. Keeping the saved version changes nothing.
**Update saved facts** is explicit, compares against the snapshot originally
previewed, archives the complete prior source-bearing JSON in `card_history`, and
updates only that card. Species identity, collection count, seen state, and
first-discovery history stay intact. The update does not speak automatically.

A stale preview fails rather than overwriting a newer edit. Invalid replacement
facts fail validation. This is local history, not a substitute for backup/export;
a history browsing/restore interface can be added under the journal tools backlog.
