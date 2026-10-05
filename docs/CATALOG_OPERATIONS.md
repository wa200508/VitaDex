# Publishing and updating the offline catalog

The app now loads validated cached publications from `<app-data>/catalog/catalog.sqlite3`
at startup, falling back to the previous valid publication and then its bundled catalog.
There is no startup network access. Personal cards retain their captured fact snapshots.
Unsupported model labels in a newer catalog are ignored by the older recognizer.

A publication contains schema version 1, a positive monotonic release number, catalog
content and review records. Each review is keyed by organism ID:

```json
{
  "organism-id": {
    "revision": 1,
    "author": "actual-author-identifier",
    "reviewer": "actual-independent-reviewer-identifier",
    "decision": "approved",
    "date": "2026-10-04"
  }
}
```

These are record shapes, not approvals. The starter catalog is draft content and will
be rejected. A curator must substantiate the factual fields, fill `fact_sources` with
URLs also present in `references`, and record independent approval of the exact revision.
Review records are distributed publicly with the catalog: use agreed public identifiers,
not private contact information. The software checks completeness, not scientific truth.

Build files locally after review:

```bash
python scripts/publish_catalog.py --catalog reviewed-catalog.json \
  --reviews reviews.json --release 1 --output artifacts/catalog
```

Upload the immutable `catalog-1-<sha256>.json` first, then `manifest.json` to the same
HTTPS origin. The manifest contains exact size, SHA-256 and release number. A deployment
must not publish the manifest before its referenced bundle is accessible. No service,
bucket, account or public endpoint has been provisioned by this implementation.

Explicit developer update (desktop, or a test harness with the app-data directory):

```bash
python scripts/update_catalog.py --manifest https://YOUR-HOST/catalog/manifest.json \
  --cache /PATH/TO/APP-DATA/catalog
```

The command is never run automatically. It rejects redirects and cross-origin bundles,
limits downloads to 8 MiB, bounds network waits, validates review metadata, and performs
an atomic SQLite transaction retaining two releases. Same/older releases are rejected.
Failures leave the active cache unchanged. The old `sync_card_db.py` now delegates to this
safe interface and no longer overwrites the fictional demo database.

Deployment still needs a chosen HTTPS origin and real reviewed content. Android manual
and WorkManager scheduling, conditional requests, signed manifests/key rotation, and
editorial database tooling remain pending. The APK still has no Internet permission.
Before enabling Android networking, finish timeout/retry behavior and test background
constraints on devices. Do not enable polling merely because the app is open.
