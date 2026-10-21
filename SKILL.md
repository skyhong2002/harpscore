---
name: harpscore
description: Create and revise playable harmonica arrangements and readable Jianpu in MuseScore. Use for harmonica score creation, beginner duet orchestration, numbered notation and engraving corrections with rendered verification.
---

# HarpScore

An agent-readable arranging and engraving skill. Read rules, inspect the actual Summer reference and the requested score's rendering, then apply the verified layout to the complete requested work. This repository is not an audio-to-score service.

## Load only the needed references

- Always: `docs/agent-contract.md`, `docs/workflow.md`, `docs/arranging.md`.
- Jianpu: `docs/jianpu.md` and the chosen profile in `profiles/`.
- Reusing the founding user's style: `docs/preferences.md` and `profiles/skyhong.json`.
- Resolving an old contradictory instruction: `docs/conversation-decisions.md`. Later explicit corrections supersede earlier requests; do not average contradictory instructions.
- MuseScore editing/export: `docs/musescore-adapter.md`. Machine-specific constraints are conditional.
- Re-engraving or checking another edition: `docs/source-verification.md`; a transcription table is an intermediate, not independent proof of the original scan.
- Starting a new piece: `docs/templates.md` and `templates/musescore/`. Check the verification record and copy the matching musical example, which contains the public-domain complete Entertainer arrangement using the copied Summer layouts, rather than an empty starter. See its exact verification record. Numbered overlays still require explicit synchronization after editing notes.
- Before delivery: `docs/verification.md`.
- First use or changed renderer/font: `docs/tryout.md`; open the actual Summer reference in MuseScore, reuse its matching layout and inspect representative passages from the requested piece. Do not create an original four-bar exercise or treat a substitute exercise as evidence for Summer's layout.

## Non-negotiable checks

Separate source transcription, musical adaptation, notation respelling and layout. A layout-only request preserves performed pitch, onset, duration and velocity. A new musical change needs a stated musical reason or user request.

Treat pickups and their arrivals as one phrase when assigning parts. A quartet's non-leading wind still needs source-aware inner lines, fills or accompaniment, not only rests. For octave/fifth/third double stops, verify the actual hole pair, common breath and slide state; record tongue blocking. Read A11–A14 in `docs/arranging.md` before using them.

For non-octave numbered double stops, reduce both digits and stack symmetrically around the ordinary numeral centre, preserving staff spacing. Scale and centre their dots/accidentals too. For the selected user's numbered-only octave shorthand, show one numeral with an explicit octave-doubling mark while retaining both performed pitches and their tie chains. Staff notation keeps both written notes. Doubling differs from a transposing ottava. See J16–J21 in `docs/jianpu.md`; hidden native notes alone do not communicate the second pitch. Keep ties/slurs close to the digits, with separate upper/lower arcs for non-octave pairs.

For solo with piano, keep the wind's full melody and score the piano as a grand staff with independent voices where notes overlap. Do not reuse a bass-harp/chord-harp reduction as if it were the original piano accompaniment. A mixed numbered-wind/native-piano score must switch notation per staff, preserve every piano voice and verify the first-page meter/tempo clearance too.

Keep phrases intact in beginner duets; do not hand off mechanically every four bars. Extend Bass notes into unnecessary tiny rests without flattening grooves such as 3+3+2. Chord carries rhythm and often offbeats; its symbols follow harmonic time, including bar starts, independently of its attacks.

Jianpu octave references alter dots, not pitch. Preserve fixed-C versus movable-do choice. Every quarter-beat underline group needs a physical gap in the actual renderer. Do not tie visibly to extension dashes. Keep x/X/0 baseline, dynamics and chord-symbol lanes separate. Compare any visual overlay with native playback notes after edits.

Preserve unrelated works and unsaved changes. Record editable-score work, PDF/audio export and cloud delivery separately, and respect the current task's pauses. Actual GUI screenshots plus normal save/reopen can verify local rendering without PDF or audio exports. Discover actual local MuseScore capabilities before conversion; stop and diagnose a failed export instead of repeatedly spawning converters. A file's existence does not prove clean export, correct rendering or verified playback.

Deliver only requested editions. Report what was checked and which checks still lack evidence. Do not claim automatic transcription, an installed generic engraving engine or a successful MuseScore trial unless actually performed.
