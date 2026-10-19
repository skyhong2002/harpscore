---
name: harpscore
description: Create and revise playable harmonica arrangements and readable Jianpu in MuseScore. Use for harmonica score creation, beginner duet orchestration, numbered notation and engraving corrections with rendered verification.
---

# HarpScore

An agent-readable arranging and engraving skill. Read rules, do a small real trial, inspect its rendering, then apply the verified approach to the complete requested work. This repository is not an audio-to-score service.

## Load only the needed references

- Always: `docs/agent-contract.md`, `docs/workflow.md`, `docs/arranging.md`.
- Jianpu: `docs/jianpu.md` and the chosen profile in `profiles/`.
- Reusing the founding user's style: `docs/preferences.md` and `profiles/skyhong.json`.
- Resolving an old contradictory instruction: `docs/conversation-decisions.md`. Later explicit corrections supersede earlier requests; do not average contradictory instructions.
- MuseScore editing/export: `docs/musescore-adapter.md`. Machine-specific constraints are conditional.
- Before delivery: `docs/verification.md`.
- First use or changed renderer/font: `docs/tryout.md`; run `python3 scripts/tryout.py --out <temporary-directory>`, open the generated MusicXML normally in MuseScore and perform the trial task. This helper creates a fixture, not a completed Jianpu renderer.

## Non-negotiable checks

Separate source transcription, musical adaptation, notation respelling and layout. A layout-only request preserves performed pitch, onset, duration and velocity. A new musical change needs a stated musical reason or user request.

Keep phrases intact in beginner duets; do not hand off mechanically every four bars. Extend Bass notes into unnecessary tiny rests without flattening grooves such as 3+3+2. Chord carries rhythm and often offbeats; its symbols follow harmonic time, including bar starts, independently of its attacks.

Jianpu octave references alter dots, not pitch. Preserve fixed-C versus movable-do choice. Every quarter-beat underline group needs a physical gap in the actual renderer. Do not tie visibly to extension dashes. Keep x/X/0 baseline, dynamics and chord-symbol lanes separate. Compare any visual overlay with native playback notes after edits.

Preserve unrelated works and unsaved changes. Respect an export pause. Discover actual local MuseScore capabilities before conversion; stop and diagnose a failed export instead of repeatedly spawning converters. A file's existence does not prove clean export, correct rendering or verified playback.

Deliver only requested editions. Report what was checked and which checks still lack evidence. Do not claim automatic transcription, an installed generic engraving engine or a successful MuseScore trial unless actually performed.
