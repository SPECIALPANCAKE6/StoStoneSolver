# StoStone Godot MVP Implementation Plan

## Goal

Build the first playable StoStone Godot 4.6.2 Standard app while keeping Python as an offline puzzle foundry only. The shipped client runtime must be GDScript-only and must not require Python, py4godot, C#, a hosted API, or server access.

## Architecture

- Python remains the authoritative development tool for generation, solving, uniqueness proof, scoring, hint-plan derivation, and pack export.
- Godot loads bundled JSON packs from `res://assets/packs/` and runs local play, local validation feedback, hints, completion matching, and prototype local progress.
- `PuzzlePack` uses ID-indexed maps so the Godot loader never depends on puzzle, solution, or hint order.
- `SolutionDTO` is allowed in `local_mvp`, `dev`, and `debug` packs only as local convenience data. It is not suitable for competitive, rewarded, paid, or server-authoritative modes.
- User-created puzzles are local drafts in the MVP. Full uniqueness proof is deferred to Python desktop validation or future hosted validation.

## File Targets

- `shared/schemas/`: JSON schema files for pack, puzzle, solution, hint, manifest, debug, and local progress DTOs.
- `src/stostone/pack_export/`: pack DTO construction, canonical hashing, hint-plan derivation, build-report output, and starter-pack defaults.
- `src/stostone/cli.py`: new `export-pack` route.
- `tests/test_pack_export.py`: canonical ID, schema shape, build-report, and CLI coverage.
- `apps/godot/stoStoneGame/`: Godot project shell, GDScript loaders/views, and bundled starter pack.
- `tasks/todo_game.md`: game milestone checklist and verification log.

## Implementation Steps

1. Add schemas and document zero-based `[row, col]` coordinates, pack classification, and schema compatibility.
2. Add canonical hash serialization with sorted keys, normalized room IDs, stable weight/given ordering, and no generated metadata.
3. Add Python pack export service and CLI.
4. Export `starter_pack.json` and `starter_pack.build_report.json`.
5. Add Godot scripts/scenes for pack loading, puzzle selection, board play, hints, completion, progress, draft creation, and drop preview.
6. Run Python tests and Godot project validation when the `godot` executable is available.

## Acceptance

- Starter pack contains at least 3 tutorial puzzles, 5 easy puzzles, 5 medium puzzles, and 1 harder showcase puzzle.
- Every bundled puzzle has a stable `puzzle_id`, unique solution proof metadata, difficulty label, source/generator metadata, and at least one deterministic hint path.
- Godot loads pack maps by ID, rejects unsupported major schema versions, tolerates unknown optional fields, and reports missing required fields clearly.
- Play supports shade/unshade, local rule feedback, hints, completion matching against local MVP solution data, progress persistence, and visible StoStone drop explanation.
