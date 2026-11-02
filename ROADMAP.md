# VitaDex roadmap

Updated 2026-11-02 after the quality and product-intent review. The detailed,
prioritized work list is [BACKLOG.md](BACKLOG.md); evidence and verification limits
are in [QUALITY_REVIEW.md](QUALITY_REVIEW.md). These supersede the older overlapping
checklists so completed prototype work is not mistaken for mobile release readiness.

## Product destination

A mobile nature companion: **discover → listen → keep → revisit → ask**.
First confirmed species discoveries introduce themselves aloud and preserve a
card. Familiar organisms stay quiet. Learning uses cited evidence; questions
should retrieve source passages for the user's chosen LLM. Power conservation
is required throughout. Computer runs are development previews; no web product
is planned. Placeholder art is allowed while core features are developed.

## What exists in the local prototype

- Five source-checked Ohio starter organisms, with human review explicitly pending.
- Simulated encounters, save-before-announcement behavior, local speech adapters,
  replay, persistent voice/seen settings, and same-key repeat suppression.
- Local SQLite snapshots with sources, journal/card views, search, filters, sorting,
  error messages, and responsive collection columns.
- Source, product, battery, and art-direction requirements; an unapproved art study
  outside runtime.
- 70 passing tests, configured lint/compile checks, and an expanded passing Kivy UI script.
- The first-five follow-up implements migration recovery, stable atomic identity,
  shared fact validation, speech lifecycle code, and incremental collection work.
  Actual-device speech/energy acceptance remains open; see
  [the follow-up report](docs/review/TOP_FIVE.md).

All of this includes local uncommitted work; it is not a published mobile release.
There is no mobile build, real-device audio/energy evidence, actual identification,
source-text retrieval, or LLM chat yet. The review found integrity gaps despite the
passing suite.

## Milestones

| Milestone | Outcome | Backlog |
| --- | --- | --- |
| 1. Integrity and first-discovery reliability | Safe migration, consistent cited facts, stable/atomic species identity, cancellable speech | VD-01–04, regression work VD-12 |
| 2. Complete five-card learning experience | Incremental collection, reviewed content workflow, readable discovery views, safe catalog updates, cited questions | VD-05/06/10/11/13/14 |
| 3. Mobile proof | Installable preview, verified native lifecycle/audio, accessibility and measured energy budgets | VD-07–09 and mobile portions of VD-14 |
| 4. Enrich and capture | Backup, personal journal tools, bounded capture, trait-focused art, more regional organisms | VD-15–20 |

Start the phone-build spike during milestone 2 rather than deferring platform risk
until every feature is complete. Do not make final art or sensing a prerequisite
for testing the core experience.

## Governing requirements

- [PRODUCT.md](PRODUCT.md): vision, discovery loop, and planned conversation.
- [SOURCE_POLICY.md](SOURCE_POLICY.md), [OHIO_STARTER.md](OHIO_STARTER.md): provenance
  and honest review/source reuse status.
- [BATTERY_POLICY.md](BATTERY_POLICY.md): bounded work and real-device validation.
- [ART_DIRECTION.md](ART_DIRECTION.md): trait-led realistic anime art, placeholders
  permitted, anatomy/rights review before final use.

Next: independent content review (VD-06), a minimal phone-build spike (VD-07/08),
and permitted source passages (VD-10). Close mobile speech and energy gates using
device evidence, rather than marking them complete from mocked tests.
