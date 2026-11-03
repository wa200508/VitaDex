# Safe catalog updates

The catalog models and validation now live in side-effect-free `catalog.py`.
`database.py` remains the application wrapper that loads the bundled catalogs.
The sync command can therefore repair a corrupt current JSON file without first
trying to import it as the application's global catalog.

```sh
python scripts/sync_card_db.py --url https://your-host/path/database.json --timeout 15
python scripts/build_corpus.py
```

The updater requires HTTPS, enforces a finite timeout and 5 MiB payload bound,
validates schema, shared field types, identity invariants, and source evidence,
then writes/fsyncs a temporary file and atomically replaces the target. Existing
bytes, even a corrupt file needed for diagnosis, are retained in `database.json.bak`
and a content-addressed `.bak.<hash>` archive, preserving earlier known versions.
HTTPS-to-HTTP redirects are rejected.
Validation or replacement failure cannot leave a partially written target.

The command is a developer/publishing utility, not an automatic background update
loop. Catalog and corpus are not published as an atomic multi-file transaction:
rebuild and test the corpus before shipping the bundle. If an interrupted manual
process leaves them inconsistent, corpus validation refuses stale evidence rather
than attaching old citations to new text. Saved cards preserve their snapshots
until their user explicitly reviews a fact update.

Tests cover invalid downloads, timeout handling, corrupt-current/valid-new repair,
interrupted replacement, and retained backups. Recovery does not automatically
promote imported source-checked material to human-reviewed status.
