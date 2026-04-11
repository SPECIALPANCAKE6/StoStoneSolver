# Todo

## Assumptions
- Verification will use smoke runs because the repo has no dedicated tests.
- The goal is a minimal correctness pass, not a redesign.

## Checklist
- [x] Inspect active solver files and search for remaining global-state dependencies.
- [x] Confirm whether tests exist and establish the smoke-run fallback.
- [x] Verify `domainBuilder.domainReduce(...)` against `gridUtils.borderGen(...)` tuple semantics.
- [x] Verify `backtrack.py` rigid-drop collision logic, bool returns, and failed-branch cleanup.
- [x] Verify `Solver.outputPUZPRE(...)` handles solved and unsolved states safely.
- [x] Apply the minimal code fixes required by the audit.
- [x] Run the `readPuzzle`/`backtrack` smoke command on `puzzles/000-000.txt`.
- [x] Run `python Solver.py` and confirm the solver progresses without immediate exceptions.
- [x] Add a review note with exact commands and outcomes.

## Discovery Notes
- No test files were found.
- No active `readPuzzle.` global attribute usage was found in solver execution code.
- `connChecker.py` already follows the `allRoomIndices` requirement.
- The worktree is already dirty in the refactor files, so edits must stay surgical.
- `puzzles/001-000-1.txt` contains pre-shaded givens, so backtracking cleanup must preserve original cell values.
- `domainGen.py` appears to be dead prototype code rather than part of the active solver flow.

## Review
- Implemented fixes:
- `domainBuilder.domainReduce(...)` now uses explicit `outside_cell` / `room_cell` names so the border comparison matches `gridUtils.borderGen(...)` semantics directly.
- `domainBuilder.unDraw(...)` can now restore from `initialState` during backtracking cleanup, which preserves required givens.
- `backtrack.canStoneDrop(...)` now requires every non-self destination cell to be empty before a rigid stone can fall one row.
- `backtrack.backtrack(...)` now restores room cells from `initialState` on failed branches and clears stale `drawnStones` entries.
- `Solver.outputPUZPRE(...)` now takes `puzzleDict` explicitly, uses direct weight-coordinate checks, skips `None` stones safely, and only writes solution files for solved puzzles.

- Commands run:
- `@' import readPuzzle, backtrack ... '@ | python -` on `puzzles/000-000.txt` before edits: `rooms: 5`, `solve: True`.
- `python Solver.py` before edits with a 20s timeout: startup and multiple puzzles progressed without immediate exceptions.
- `@' import readPuzzle, domainBuilder ... '@ | python -` after edits on `puzzles/001-000-1.txt`: `givens_restored: True`.
- `@' import backtrack ... '@ | python -` after edits with a blocked rigid-drop scenario: `blocked_drop: False`.
- `@' import readPuzzle, backtrack ... '@ | python -` after edits on `puzzles/000-000.txt`: `rooms: 5`, `solve: True`.
- `python Solver.py` after edits with a 5s timeout: progressed cleanly through the early puzzle set, including `001-000-1.txt` with givens, with no immediate exceptions.
- Focused validation on `puzzles/001-001.txt` exposed a false-positive Sto-Stone acceptance: the rigid-drop result satisfied per-column counts but did not fill the contiguous bottom half.
- Added `fillsBottomHalf(...)` in `backtrack.py` and switched the final Sto-Stone acceptance check to use it instead of column counts alone.
- `@' ... detailed validation for puzzles/001-001.txt ... '@ | python -` before the final fix: `solve: True`, with a top-half fill mismatch after the rigid drop.
- `@' import readPuzzle, backtrack ... '@ | python -` after the final fix on `puzzles/001-001.txt`: `solve: False`.
- `python Solver.py` after the final fix with a 5s timeout: `001-001.txt` now logs `Backtracking exhausted without finding a solution.` and the run continues without immediate exceptions.
- `solutions/001-001-solved.txt` still exists from the earlier false-positive run and is now stale.
- Further focused debugging on `001-001` found the remaining false-negative in the rigid-drop loop: `isStoStone(...)` cached droppability per stone and only refreshed it for stones that had already moved, so stones that became movable after lower stones fell could remain incorrectly stuck.
- Rewrote the `isStoStone(...)` drop loop to recompute each stone's downward move from the current board state on every pass.
- `@' import readPuzzle, backtrack ... '@ | python -` after the drop-loop fix on `puzzles/001-001.txt`: `solve: True`, and the final board is the exact bottom half filled.
- `@' import readPuzzle, backtrack ... '@ | python -` after the drop-loop fix on `puzzles/000-000.txt`: `solve: True`.
- `python Solver.py` after the drop-loop fix with a 5s timeout: `001-001.txt` now logs `Puzzle was solved successfully.` and the run continues without immediate exceptions.

## README Refresh

### Checklist
- [x] Re-verify the CLI commands and output snippets that will be documented.
- [x] Add a root `README.md` framed as the thesis solver foundation for future generator and game work.
- [x] Document current capabilities, puzzle format, solver flow, repository layout, and roadmap.
- [x] Re-run the documented commands to confirm the examples still match the live CLI.

### Review
- Added `README.md` as the new project entry document.
- Framed the repository explicitly as the revived thesis solver, with the solver positioned as the foundation for future generator and playable game work.
- Documented the current CLI surface, solve modes, PUZ-PRE puzzle inputs, solved-file output behavior, and active solver modules.
- Added a staged roadmap that keeps generator and game work clearly future-facing.
- Commands rechecked for the README:
- `python Solver.py --help`
- `python Solver.py list`
- `python Solver.py show 000-000`
- `python Solver.py solve 000-000 --solutions-dir solutions`

## KISS / DRY Cleanup

### Checklist
- [x] Split lightweight puzzle metadata reads from full solver precomputation.
- [x] Remove `backtrack.py` scratch-state coupling on injected `lastPlaced`.
- [x] Collapse duplicate connectivity and legacy domain helpers onto shared utilities.
- [x] Simplify PUZ-PRE export loops without changing solved-file behavior.
- [x] Re-run CLI smoke commands for metadata and solving.

### Review
- Added `readPuzzle._readPuzzleSections(...)` so the PUZ-PRE section parsing is shared by both the full loader and the new lightweight metadata reader.
- Added `readPuzzle.readPuzzleMetadata(...)` and switched `solver_runner.summarize_puzzle(...)` to use it, so `python Solver.py show ...` no longer builds room domains or mutable solver state.
- Simplified `solver_runner.output_puzpre(...)` with one grid-writing helper plus precomputed weight and filled-cell lookups instead of repeating three near-identical nested loops.
- Removed the runtime-injected `puzzleDict['lastPlaced']` scratch key from `backtrack.py`; Sto-Stone drop bookkeeping now stays local inside `isStoStone(...)`.
- Replaced `connChecker.py`'s duplicate BFS with a thin call to `gridUtils.isConnected(...)`.
- Replaced the stale `domainGen.py` prototype with a compatibility wrapper around `gridUtils.connectedSubgrids(...)`, eliminating its old dependency on `readPuzzle` globals.
- Commands run:
- `python Solver.py show 000-000` -> reported the expected puzzle metadata successfully.
- `python Solver.py solve 000-000 --solutions-dir solutions` -> solved successfully and wrote `solutions/000-000-solved.txt`.
- `python -c "import readPuzzle, backtrack; p = readPuzzle.readPuzzle('puzzles/000-000.txt'); print('lastPlaced_before', 'lastPlaced' in p); print('solve', backtrack.backtrack(0, p)); print('lastPlaced_after', 'lastPlaced' in p)"` -> `lastPlaced_before False`, `solve True`, `lastPlaced_after False`.
