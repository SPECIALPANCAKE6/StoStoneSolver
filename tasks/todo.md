# Todo

## Assumptions
- This phase is a structural reorganization, not a solver-rule rewrite.
- Verification is smoke-only; the current pytest suite is out of scope.
- Top-level entry modules remain as compatibility shims over the new package API.

## Checklist
- [x] Add package/project scaffolding for an installable `src/stostone/` layout.
- [x] Introduce dataclass models for puzzle metadata, immutable spec, derived room cache, mutable puzzle state, aggregate puzzle, and solve results.
- [x] Move PUZ-PRE parsing and export into `stostone.io`.
- [x] Move grid and domain helpers into `stostone.core`.
- [x] Move state mutation, validation, and backtracking into `stostone.solver`.
- [x] Add generator-facing seams for in-memory puzzle construction and state reset without implementing generation algorithms.
- [x] Replace the active root modules with compatibility shims over the new package.
- [x] Run the approved smoke commands and capture exact outcomes.

## Discovery Notes
- The repo already has a small CLI split between `Solver.py`, `solver_cli.py`, and `solver_runner.py`.
- The active solver still centers on a mutable puzzle dictionary; this task migrates the internal implementation to dataclasses while preserving the existing low-level shapes.
- A pytest suite exists today, but it is not part of this phase's success criteria.

## Review
- Added `pyproject.toml` and a new `src/stostone/` shared package with dataclass-based models, parser/export IO, core grid/domain helpers, solver modules, generator-facing seams, and a package-native CLI.
- Follow-up tree cleanup moved the compatibility wrappers into `src/stostone/compat/` and moved the remaining root helper modules into package directories under `src/stostone/core/` and `src/stostone/solver/`.
- Simplified the repo root so only `Solver.py`, project metadata/config, docs, and major workspace directories remain.
- Added a root `stostone/` shim package so `python -m stostone.cli ...` works from the repo root without needing an install step.
- Added `docs/architecture.md` and moved the old solved sample files into `docs/examples/legacy-solutions/`.
- Resolved one packaging bug discovered during smoke verification: `solver.__init__` was importing `service`, which created a circular import through `generator` and `io`; the package init was reduced to a lightweight solver export surface.

### Commands Run
- `python -c "import stostone, solver_cli, solver_runner, readPuzzle, backtrack; print('imports ok')"` -> `imports ok`
- `python Solver.py --help` -> rendered the expected `list/show/solve` CLI usage
- `python -m stostone.cli --help` -> rendered the expected package CLI usage
- `python Solver.py list` -> listed the bundled puzzle files successfully
- `python Solver.py show 000-000` -> reported the expected metadata for `000-000.txt`
- `python -c "from stostone import load_puzzle, solve_puzzle; puzzle = load_puzzle('puzzles/000-000.txt'); result = solve_puzzle(puzzle); print(type(puzzle).__name__, type(result).__name__, result.solved, result.mode)"` -> `Puzzle SolveResult True sto-stone`
- `python Solver.py solve 000-000` -> solved successfully
- `python -m stostone.cli solve 000-000` -> solved successfully
- `python -c "import readPuzzle, backtrack; puzzle = readPuzzle.readPuzzle('puzzles/000-000.txt'); print('rooms', puzzle['rooms']); print('solve', backtrack.backtrack(0, puzzle)); print('checks', puzzle['constraintChecks'])"` -> `rooms 5`, `solve True`, `checks 40`
- `python -c "from stostone.compat import readPuzzle, backtrack; puzzle = readPuzzle('puzzles/000-000.txt'); print('rooms', puzzle['rooms']); print('solve', backtrack(0, puzzle))"` -> `rooms 5`, `solve True`
