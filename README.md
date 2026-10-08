# VitaDex scientific catalog publications

Public data endpoint for VitaDex testing. These are catalog data revisions, not
versioned application releases. Application test APKs remain GitHub Actions artifacts.

No reviewed scientific catalog is published yet. `manifest.json` explicitly reports
`awaiting_review`; no draft facts or fabricated approval records are served here.

After independent scientific review, the development repository workflow validates
`data/reviewed/catalog.json`, `reviews.json`, and `release.json`, commits a new immutable
`catalog-<number>-<sha256>.json` together with its manifest, and pushes this branch
without forcing history. Previous bundles remain accessible.

Host: https://raw.githubusercontent.com/wa200508/VitaDex/codex/catalog-publications/manifest.json

Personal photos and collections are never hosted here. Review records in publications
are public: use agreed public identifiers rather than private contact information.
