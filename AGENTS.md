# HarpScore agent entrypoint

HarpScore is an agent skill and shared knowledge base for serious harmonica arranging and Jianpu engraving. The website is a distribution surface, not the product's primary intelligence. Read `SKILL.md` for conditional reference loading.

## When making music

Read `docs/guide/agent-contract.md`, `docs/guide/workflow.md` and `docs/rules/arranging.md`. For Jianpu read `docs/rules/jianpu.md` and the chosen profile. To reuse the founding user's style read `docs/history/preferences.md`; use `docs/history/conversation-decisions.md` to resolve superseded requirements. Before delivery read `docs/rules/verification.md`.

Keep performed pitch, onset, duration and velocity unchanged for layout-only tasks. Preserve phrases in beginner duets, Bass grooves and Chord's rhythmic role. Validate the actual renderer, not only logical grouping. A native-note/text overlay must remain semantically synchronized. Follow `docs/guide/tryout.md`: inspect the actual Summer reference, copy its verified layout, then check representative passages from the requested piece. Do not generate an original four-bar exercise.

## When maintaining this repository

Read `docs/maintaining.md`. `SKILL.md`, `docs/`, profiles and original fixtures are canonical. Build creates the website and portable skill ZIP from them. Keep references relative and runnable after installation. Do not add a fake transcription engine, fabricate verification or substitute stale score thumbnails.

The current naming is HarpScore (display), harpscore (repository and skill). Keep user requests, profiles and piece-specific exceptions distinct. The decision ledger preserves the history; the current contract selects which decisions to execute.

Preserve unrelated works and unsaved changes. Discover local MuseScore capabilities before exporting; do not repeatedly spawn a known crashing converter or suppress OS crash reports. Export pauses apply to their task, not every user forever.

Public source uses MIT. Do not commit credentials, private paths, unrelated chats or third-party editable scores/audio. User-authorized demo images in [site/public/images/summer/](https://skyhong2002.github.io/harpscore/images/summer/) are a specific presentation exception with separate attribution/license scope. They do not grant permission to distribute the underlying music as MIT.
