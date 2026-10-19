# Agent entrypoint

This project helps humans and agents collaborate on playable harmonica arrangements. Its current release is a documented workflow and brief builder, not a general transcription or engraving engine.

Read `docs/workflow.md` and `docs/arranging.md`. Read `docs/jianpu.md` when producing numbered notation, `docs/verification.md` before delivery, and `docs/project.md` when changing the toolkit itself. Load only the selected profile under `profiles/`.

## Working contract

- The user's current musical intent overrides a preset. Preserve unrelated pieces and unsaved edits. Discover local application constraints before invoking an exporter.
- Separate source transcription, musical adaptation, visual engraving and audio rendering. A layout-only request must not alter pitches, onsets, durations or velocities.
- A beginner arrangement is an explicit target, not the universal default. Keep phrases intact; do not alternate duet voices mechanically by bar count.
- Choose actual instrument models, playable sounding ranges and concert/written pitch before arranging. Numbered-notation octave references are presentation settings, not transpositions.
- For Jianpu, follow the selected tonic system. Preserve performed events and verify the visible overlay against the native score when using transparent playback anchors.
- Group underlines within each quarter beat and inspect physical rendered gaps. Logical grouping alone does not prove that lines are separate.
- Deliver only the requested editions. Keep one active file per edition, archive previous revisions separately, and keep sources, audio and exports with the same piece.
- Describe evidence accurately: XML validation, rendered notation, playback, exported files and public deployment are different checks. Record unverified items.

## Public contributions

Keep universal rules in docs and preferences in profiles. Add a minimal original fixture when fixing an engraving defect. Never commit third-party music/audio, private filesystem paths, credentials or machine-specific crash workarounds to universal defaults. Do not bundle any existing Summer score.

The user-authorized rendered demo images in `web/assets/` are a specific exception for website presentation. Keep attribution and their exclusion from the MIT license in NOTICE.md; they do not authorize bundling editable scores or recordings.
