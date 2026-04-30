# StoStone Godot MVP Todo

## Assumptions

- Godot runtime code is GDScript-only.
- Python is an offline foundry and development/export tool only.
- Starter packs are `local_mvp` packs and may ship local convenience solutions.
- Public or competitive future packs must not rely on shipped `SolutionDTO` data.
- All coordinates are zero-based `[row, col]`.

## Checklist

- [x] Capture the approved implementation plan in `implementation_plan.md`.
- [x] Create a game-specific task checklist in `tasks/todo_game.md`.
- [x] Add shared JSON schemas for pack, puzzle, solution, hints, manifest, debug, and progress DTOs.
- [x] Implement canonical puzzle hashing from deterministic content-only JSON.
- [x] Add Python pack exporter service and `Solver.py export-pack` route.
- [x] Add exporter tests for schema shape, canonical IDs, build reports, and CLI output.
- [x] Export the MVP starter pack and sibling build report.
- [x] Build the Godot project shell under `apps/godot/stoStoneGame`.
- [x] Add GDScript pack loading, puzzle select, play board, hints, completion, progress, drafts, and drop preview.
- [x] Run Python verification.
- [x] Run Godot verification or record why it could not be run.

## Review

- Added JSON schemas in `shared/schemas/` with pack classification, zero-based coordinates, local-MVP solution warnings, and ID-indexed pack maps.
- Added `stostone.pack_export` and the `Solver.py export-pack` route. The exporter computes content-only canonical puzzle IDs, proves uniqueness, derives hint plans, writes pack JSON, and writes a sibling build report.
- Exported `apps/godot/stoStoneGame/assets/packs/starter_pack.json` with 14 puzzles: 3 tutorial, 5 easy, 5 medium, and 1 showcase.
- Added a Godot shell with pack loading, puzzle selection, board rendering, shade/unshade input, local rule feedback, deterministic hints, completion matching, prototype progress/unlocks, draft save, and drop preview.
- Python verification passed with `84 passed`.
- Godot headless verification was not run because no `godot` or `Godot_v4.6.2-stable_win64.exe` command was available on PATH.

## Commands Run

- `python -m pytest tests\test_pack_export.py` -> `5 passed in 0.52s`
- `python Solver.py export-pack --puzzles 000-001.txt --out test-output\verify-pack.json` -> wrote pack and build report
- `python -m pytest` -> `84 passed in 4.26s`
- `python -m json.tool apps\godot\stoStoneGame\assets\packs\starter_pack.json` -> valid JSON
- `python -m json.tool apps\godot\stoStoneGame\assets\packs\starter_pack.build_report.json` -> valid JSON
- `Get-ChildItem shared\schemas\*.json | ForEach-Object { python -m json.tool $_.FullName }` -> all schema JSON files valid
- `git diff --check` -> no whitespace errors
- `Get-Command godot -ErrorAction SilentlyContinue` -> no command found
- `Get-Command Godot_v4.6.2-stable_win64.exe -ErrorAction SilentlyContinue` -> no command found
- Starter-pack acceptance script -> schema `1.0.0`, type `local_mvp`, categories `tutorial=3`, `easy=5`, `medium=5`, `showcase=1`, and 14 solutions/hint plans for 14 puzzles
