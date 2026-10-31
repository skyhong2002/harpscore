---
name: harpscore
description: Create and revise playable harmonica arrangements and readable Jianpu in MuseScore. Use for harmonica score creation, beginner duet orchestration, numbered notation and engraving corrections with rendered verification.
---

# HarpScore

An agent-readable arranging and engraving skill. Read rules, inspect the actual Summer reference and the requested score's rendering, then apply the verified layout to the complete requested work. This repository is not an audio-to-score service.

## Load only the needed references

- Always: `docs/guide/agent-contract.md`, `docs/guide/workflow.md`, `docs/rules/arranging.md`.
- Jianpu: `docs/rules/jianpu.md` and the chosen profile in `profiles/`.
- Reusing the founding user's style: `docs/history/preferences.md` and `profiles/skyhong.json`.
- Resolving an old contradictory instruction: `docs/history/conversation-decisions.md`. Later explicit corrections supersede earlier requests; do not average contradictory instructions.
- Uneven or colliding adjacent Jianpu staves: read `docs/engraving/adaptive-spacing.md`; use `tools/adaptive_staff_spacing.py` with fresh renderer geometry to expand only systems that need space.
- MuseScore editing/export: `docs/engraving/musescore-adapter.md`. Machine-specific constraints are conditional.
- Re-engraving or checking another edition: `docs/rules/source-verification.md`; a transcription table is an intermediate, not independent proof of the original scan.
- Starting a new piece: `docs/guide/starting-a-piece.md` and `pieces/entertainer/scores/`. Check the verification record and copy the matching musical example, which contains the public-domain complete Entertainer arrangement using the copied Summer layouts, rather than an empty starter. See its exact verification record. Numbered overlays still require explicit synchronization after editing notes.
- Before delivery: `docs/rules/verification.md`.
- First use or changed renderer/font: `docs/guide/tryout.md`; open the actual Summer reference in MuseScore, reuse its matching layout and inspect representative passages from the requested piece. Do not create an original four-bar exercise or treat a substitute exercise as evidence for Summer's layout.

## Non-negotiable checks

Separate source transcription, musical adaptation, notation respelling and layout. A layout-only request preserves performed pitch, onset, duration and velocity. A new musical change needs a stated musical reason or user request.

For skyhong's Double Bass harmonica, use a bass F clef with 8 below in staff notation, with no duplicate octave transposition. Playback combines each low fundamental with its upper octave at -10 dB relative gain, synchronized through ties and dynamics. Treat this as an octave-reed timbre, not an extra written double stop; avoid duplicating a layer already in the sound. Decibels are not MIDI velocity offsets. Read A08a–A08b and V23; verify sounding pitch and the actual playback separately.

Treat pickups and their arrivals as one phrase when assigning parts. A quartet's non-leading wind still needs source-aware inner lines, fills or accompaniment, not only rests. For octave/fifth/third double stops, verify the actual hole pair, common breath and slide state; record tongue blocking. Read A11–A14 in `docs/rules/arranging.md` before using them.

For non-octave numbered double stops, reduce both digits and stack symmetrically around the ordinary numeral centre, preserving staff spacing. Scale and centre their dots/accidentals too. For the selected user's numbered-only octave shorthand, show one numeral with an explicit octave-doubling mark while retaining both performed pitches and their tie chains. Staff notation keeps both written notes. Doubling differs from a transposing ottava. See J16–J21 in `docs/rules/jianpu.md`; hidden native notes alone do not communicate the second pitch. Keep ties/slurs close to the digits, with distinct arcs for non-octave pairs according to the selected profile. The current skyhong preference puts every visible connection above the numerals as a shallow arch, centre above the ends; it supersedes the earlier upper/lower split. `up=up` alone does not prove the edited curve is arch-shaped: inspect short spans and continuations for inversion, inflection and excessive rise.

For solo with piano, keep the wind's full melody and score the piano as a grand staff with independent voices where notes overlap. Do not reuse a bass-harp/chord-harp reduction as if it were the original piano accompaniment. A mixed numbered-wind/native-piano score must switch notation per staff, preserve every piano voice and verify the first-page meter/tempo clearance too.

Keep phrases intact in beginner duets; do not hand off mechanically every four bars. Extend Bass notes into unnecessary tiny rests without flattening grooves such as 3+3+2. Chord carries varied rhythmic and string-ostinato roles; its symbols follow harmonic time independently of its attacks. Review full written values, audible playback and selective accent contrast under V17–V19. Keep redundant reading advice and production notes off the score (V20).

Jianpu octave references alter dots, not pitch. Preserve fixed-C versus movable-do choice. Every quarter-beat underline group needs a physical gap in the actual renderer. Do not tie visibly to extension dashes. Keep x/X/0 baseline, dynamics and chord-symbol lanes separate. Compare any visual overlay with native playback notes after edits.

Centre staccato dots and accents directly above the visible numeral (or x/X), using the rendered digit ink rather than the hidden native notehead or the accidental-plus-digit group. Check horizontal alignment separately from vertical clearance; see J08a and V04a.

For denser Jianpu, vary bars per system with actual attack density and verify real automatic wrapping. Keep triplet brackets and their labels close to their own digits. Reflow invalidates old per-system curve handles; recheck every continuation of ties, slurs, octave guides and hairpins against the new rendering. See J23–J24 and V14.

For the skyhong profile, keep the number of systems consistent across ordinary full pages of the same edition. Choose the target for the notation and instrumentation; this does not require equal bars per system. Only verified space needs from unusual notation justify fewer systems on an ordinary page. Title and incomplete final pages are separate cases. Check actual page-by-page system counts and document exceptions under V21.

Preserve unrelated works and unsaved changes. Record editable-score work, PDF/audio export and cloud delivery separately, and respect the current task's pauses. Actual GUI screenshots plus normal save/reopen can verify local rendering without PDF or audio exports. Discover actual local MuseScore capabilities before conversion; stop and diagnose a failed export instead of repeatedly spawning converters. A file's existence does not prove clean export, correct rendering or verified playback.

Deliver only requested editions. Report what was checked and which checks still lack evidence. Do not claim automatic transcription, an installed generic engraving engine or a successful MuseScore trial unless actually performed.
