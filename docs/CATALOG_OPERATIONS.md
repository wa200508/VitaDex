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
must not publish the manifest before its referenced bundle is accessible. The initial public host is the dedicated `codex/catalog-publications` branch in this
repository, served over HTTPS by GitHub. Bundles and manifest appear in one Git commit.

Explicit developer update (desktop, or a test harness with the app-data directory):

```bash
python scripts/update_catalog.py --manifest https://YOUR-HOST/catalog/manifest.json \
  --cache /PATH/TO/APP-DATA/catalog
```

The command is never run automatically. It rejects redirects and cross-origin bundles,
limits downloads to 8 MiB, bounds network waits, validates review metadata, and performs
an atomic SQLite transaction retaining two releases. Already-installed releases skip the bundle download; attempts to install older snapshots are rejected.
Failures leave the active cache unchanged. The old `sync_card_db.py` now delegates to this
safe interface and no longer overwrites the fictional demo database.

## Public test host and app update button

The fixed app endpoint is:
`https://raw.githubusercontent.com/wa200508/VitaDex/codex/catalog-publications/manifest.json`.
It currently reports `awaiting_review`, with no release number or scientific bundle.
The four-organism draft is **not** published, approved, or silently activated.

On Home, choose **Check for catalog updates**, then **Check now**. The dialog explains
network use (up to 8 MiB) and that photos/collections stay local. The one-worker check
runs off the UI thread, verifies TLS using a packaged certifi CA bundle, and validates
size/checksum/review records before committing a snapshot. Offline errors keep the
existing guide. Successful updates take effect on the next app launch; existing cards
retain their original facts. INTERNET is declared for this explicit download; there is
no startup, scan-triggered or periodic networking. A check already started when the app
closes may finish storing its validated snapshot, with no callback into the closed UI.

After actual independent review, commit these three files to the development branch:

- `data/reviewed/catalog.json`: complete reviewed catalog, not an incremental patch.
- `data/reviewed/reviews.json`: actual exact-revision review records.
- `data/reviewed/release.json`: `{"release": 1}`, increasing for each publication.

The **Publish reviewed catalog** workflow validates them and pushes the public branch
without force. A retry accepts only byte-identical content for an existing publication
number. Missing or draft approvals fail before any public files change. No input files
means bootstrap/preserve the awaiting-review manifest, never invent an empty release.
Removing all input files preserves any existing publication. Do not force-push the host
branch or edit immutable bundles. Review access is controlled by repository write access;
software validates the records but cannot authenticate a human review. This is a test
host backed by GitHub files; a production CDN and signed manifests remain future work.

Before the first publication, review recognition coverage as well as facts: publications
replace the full catalog, and the current draft has no model-label mappings. Publishing
only those four entries would provide no recognized categories with the current model.
Scientific approval and model support are separate requirements.

WorkManager scheduling, conditional requests, signed manifests/key rotation, editorial
database tooling, and real-device networking/battery validation remain pending. The new
workflow can run on relevant development-branch pushes; its manual Run workflow control
will be available after the workflow is also on the default branch.
