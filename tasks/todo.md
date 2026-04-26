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

## Current Task: Pytest Suite

### Assumptions
- The current `src/stostone` package layout is now the authoritative runtime surface to test.
- The suite should prefer tracked puzzle fixtures already in `puzzles/` instead of depending on ad hoc local files.
- Marker support should be first-class so narrow test runs are easy during solver debugging.

### Checklist
- [x] Add pytest dependency/config for the current repo layout.
- [x] Add shared fixtures for puzzle paths and writable test output directories.
- [x] Add unit tests for models, core helpers, state ops, and validation helpers.
- [x] Add integration/regression tests for PUZ-PRE IO, solver service flows, and compatibility wrappers.
- [x] Add CLI tests for `list`, `show`, and `solve`.
- [x] Run `python -m pytest` and record outcomes.

### Review
- Added `requirements.txt` with `pytest` and a `pytest.ini` that registers `unit`, `integration`, `regression`, `cli`, and `slow` markers.
- Added a new `tests/` suite covering models, core helpers, PUZ-PRE IO, solver state ops, validation helpers, solve services, compatibility wrappers, and the `Solver.py` CLI.
- Added a repo-owned `workspace_tmp_dir` fixture so tests can write outputs without depending on pytest's Windows temp cleanup behavior in this OneDrive-backed workspace.
- Verified the full suite with `python -m pytest`.

### Commands Run
- `python -m pytest` -> `32 passed in 0.93s`

## Current Task: Uniqueness Counting For Generation

### Assumptions
- The generator needs a bounded solution-count path, not just another boolean solve wrapper.
- The existing single-solution `solve_puzzle(...)` path should stay optimized for "stop at first solution".
- Uniqueness proof only needs to search up to a caller-supplied limit, with `2` as the practical generation default.

### Checklist
- [x] Add a bounded solution-count search path alongside the current boolean backtracking path.
- [x] Expose solution-count helpers from the solver service and package root for generator use.
- [x] Preserve correct board restoration while counting Sto-Stone solutions across multiple branches.
- [x] Add regression coverage for zero/one/multiple-solution counting behavior and limit handling.
- [x] Run focused verification and capture exact outcomes.

### Review
- Added `solver.search.count_solutions(...)` as a bounded recursive search that keeps the existing `backtrack(...)` fast path intact.
- Added `SolutionCountResult`, `count_puzzle_solutions(...)`, and `count_puzzle_file_solutions(...)` so the generator can ask for `0`, `1`, or `2+` solutions without re-timing or re-wrapping the solver itself.
- Preserved board correctness while counting by snapshot/restoring the grid around successful Sto-Stone validation leaves, since `is_sto_stone(...)` intentionally leaves the dropped final board in place on success for the normal solve path.
- Extended the compatibility layer with `countSolutions(...)` and `count_puzzle_solutions(...)` wrappers so the old surface is not missing the new capability.
- Added regression tests for invalid limits, zero-solution cases, bounded multi-solution counting with early stop, known unique puzzle counting, and the compatibility wrappers.
- Verified that `puzzles/000-000.txt` is not unique under the current rules (`solution_count == 2` with `limit=2`), while `puzzles/000-001.txt` is unique (`solution_count == 1` with `limit=2`).

### Commands Run
- `python -m pytest tests\test_solver_service.py tests\test_compat.py tests\test_models.py` -> `21 passed in 0.51s`
- `python -c "from src.stostone.solver.service import count_puzzle_file_solutions; result = count_puzzle_file_solutions('puzzles/000-001.txt', limit=2); print(result.solution_count, result.is_unique, result.puzzle.state.constraint_checks if result.puzzle else None)"` -> `1 True 80`
- `python -c "from src.stostone.solver.service import count_puzzle_file_solutions; result = count_puzzle_file_solutions('puzzles/000-000.txt', limit=2); print(result.solution_count, result.limit_reached, result.puzzle.state.constraint_checks if result.puzzle else None)"` -> `2 True 49`
- `python -m pytest` -> `39 passed in 1.15s`
- `python -c "import stostone; result = stostone.count_puzzle_file_solutions('puzzles/000-001.txt', limit=2); print(result.solution_count, result.is_unique)"` -> `1 True`

## Current Task: Experimental Unique Puzzle Generation

### Assumptions
- The first generator slice should prioritize a working, seedable API over a broad UI or CLI surface.
- Most generated puzzles should start with an empty `initial_state`, with non-empty reveals kept explicit and rare.
- The solver's uniqueness counter is the acceptance filter; generator candidates should be cheap to reject before any richer quality tuning.

### Checklist
- [x] Add a real generator service that can build random connected room layouts and numbered-room candidates.
- [x] Use the uniqueness-count API to reject non-unique candidates and return only uniquely solvable puzzles.
- [x] Support a mostly-empty reveal policy plus explicit `empty`, `single-cell`, and `full-room` reveal options.
- [x] Record generation metadata on the emitted puzzle and expose a generation result object.
- [x] Add focused tests and run generator smoke verification.

### Review
- Added `stostone.generator.service.generate_unique_puzzle(...)`, a seedable API that builds random connected room layouts, assigns positive room weights summing to half the board, and accepts only candidates with exactly one solution under the bounded solution-count path.
- Added `GenerationResult` plus generator metadata tracking for seed, attempts, elapsed time, reveal policy, given shaded cells, and uniqueness settings.
- Added `assembly.apply_initial_state_constraints(...)` so generated puzzles with non-empty givens constrain room domains the same way file-loaded puzzles already do.
- Added reveal policies for `mostly-empty`, `empty`, `single-cell`, and `full-room`. The default `mostly-empty` policy currently resolves to `empty` 80% of the time, `single-cell` 15% of the time, and `full-room` 5% of the time.
- Updated package exports and repo docs so the generator API is now part of the public package surface.

### Commands Run
- `python -m pytest tests\test_generator.py tests\test_solver_service.py tests\test_models.py` -> `20 passed in 0.51s`
- `python -c "from src.stostone.generator import generate_unique_puzzle; result = generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=20); print(result.attempts, result.applied_reveal_policy, result.given_shaded_cells, result.puzzle.spec.metadata.extra_fields['generator_seed'])"` -> `11 empty 0 0`
- `python -m pytest` -> `44 passed in 2.36s`
- `python - <<'PY' ... stostone.generate_unique_puzzle(...); stostone.write_puzpre(...); print(...)` -> `11 empty 0 True`
- `python -c "import stostone; puzzle = stostone.load_puzzle('artifacts/generated-smoke-4x4.txt'); result = stostone.count_puzzle_solutions(puzzle, limit=2); print(result.solution_count, puzzle.spec.metadata.author, puzzle.spec.metadata.extra_fields['generator_seed'])"` -> `1 StoStoneSolver Generator 0`

## Current Task: Generate CLI Route

### Assumptions
- The CLI should remain a thin route over `stostone.generator.generate_unique_puzzle(...)`.
- Generated files should be written explicitly by caller-provided output path to avoid surprise repository writes.
- The existing uniqueness-gated generator behavior should not be changed in this slice.

### Checklist
- [ ] Add a `generate` subcommand that accepts puzzle size, room count, seed, attempt budget, reveal policy, solve mode, and output path.
- [ ] Write generated puzzles through the existing PUZ-PRE output layer while preserving generated initial-state givens.
- [ ] Add CLI regression coverage for a seeded generated puzzle.
- [ ] Update README usage examples for the new route.
- [ ] Run focused and full verification and capture outcomes.

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

## Current Task: Generator Corpus Tooling And Engine API

### Assumptions
- Batch generation should stay a thin orchestration layer over the existing seeded generator instead of becoming a separate search implementation.
- Corpus quality gates should be cheap to evaluate after uniqueness is proven, using derived room metrics plus a re-solve pass for iteration counts.
- Future desktop/mobile callers should use an in-process engine surface instead of importing CLI routines.

### Checklist
- [x] Extend the generator service with batch corpus generation, output writing, duplicate detection, and optional summary export.
- [x] Add quality metrics and generation filters for room balance, shape compactness, reveal limits, solve iterations, and difficulty score.
- [x] Add a thin engine API for `load`, `summarize`, `solve`, `count`, `generate`, and `generate_corpus`.
- [x] Add regression coverage for the batch CLI route and the engine API boundary.
- [x] Run focused and full verification and capture exact outcomes.

### Review
- Extended `stostone.generator.service` from single-puzzle generation into corpus orchestration with `build_puzzle_corpus(...)`, duplicate detection against existing outputs, optional JSON summary export, and write helpers that keep generated puzzle output under the normal PUZ-PRE path.
- Added `GenerationQuality`, `GenerationFilters`, `GenerationBatchItem`, and `GenerationBatchResult`, then scored each generated puzzle with room-balance, compactness, reveal-count, solve-iteration, and derived difficulty metrics before applying optional quality gates.
- Added `stostone.engine` as the app-facing in-process boundary for `load`, `summarize`, `solve`, `count`, `generate`, and `generate_corpus`, so future desktop/mobile callers do not need to depend on CLI parsing or logging setup.
- Expanded regression coverage with a batch `Solver.py generate` test that writes a two-puzzle corpus plus summary file, and a dedicated engine test module that exercises both solver and generator entrypoints.
- Fixed one generator bug discovered during verification: the quality-scoring clone path was reusing nested mutable puzzle state through `to_legacy_dict()`, which leaked solved-state mutations back into generated puzzles until the clone was switched to a deep copy.

### Commands Run
- `python -m pytest tests\test_generator.py tests\test_cli.py tests\test_engine.py tests\test_models.py` -> initially failed with 5 generator regressions caused by shared mutable state in the generation clone path
- `python -m pytest tests\test_generator.py tests\test_cli.py tests\test_engine.py tests\test_models.py` -> `23 passed in 1.55s`
- `python -m pytest` -> `54 passed in 2.12s`

## Current Task: Greedy Clue Carving For Generation

### Assumptions
- Clue carving in this slice means minimizing numbered-room clues, not reveal-policy givens, so the existing `empty` / `single-cell` / `full-room` semantics remain meaningful.
- The generator should keep uniqueness proof as the hard gate after every clue-removal attempt.
- Generated unsolved puzzles with givens must round-trip through PUZ-PRE export without depending on solved-state `drawnStones`.

### Checklist
- [x] Add a greedy post-generation clue-carving pass that removes numbered-room clues while uniqueness stays `1`.
- [x] Surface final numbered-room counts and carving metadata on generation results.
- [x] Expose a simple opt-out switch through the engine and CLI.
- [x] Fix PUZ-PRE writing so unsolved generated givens persist on disk.
- [x] Add focused regressions and rerun focused plus full verification.

### Review
- Added a greedy numbered-room clue-carving pass to `generate_unique_puzzle(...)`: starting from the constructive solution-first candidate, it shuffles room order by seed and removes each room number only if the puzzle remains uniquely solvable under the bounded counter.
- Extended `GenerationResult` with final and pre-carving numbered-room counts plus carving-check metadata so corpus summaries and CLI output can report what the minimization pass actually changed.
- Threaded carving through `stostone.engine` and the CLI, with carving enabled by default and `--no-clue-carving` as the explicit opt-out path.
- Fixed `write_puzpre(...)` for unsolved generated puzzles by falling back to `spec.initial_state` when no solved `drawnStones` exist, so generated givens now survive round-trip to disk.
- Added regressions for default clue carving, unsolved-given PUZ-PRE round-tripping, and the CLI opt-out path.

### Commands Run
- `python -m pytest tests\test_generator.py tests\test_io_puzpre.py tests\test_cli.py tests\test_engine.py tests\test_models.py` -> initially failed with 1 regression due to `pre_solved_rooms` being recomputed from room area instead of preserved reveal-policy semantics
- `python -m pytest tests\test_generator.py tests\test_io_puzpre.py tests\test_cli.py tests\test_engine.py tests\test_models.py` -> `29 passed in 6.95s`
- `python -m pytest` -> `57 passed in 7.41s`

## Current Task: Reveal Policy Distribution Tuning

### Assumptions
- The user wants pre-shaded starts to stay uncommon, but not vanishingly rare.
- The `mostly-empty` policy should remain the default reveal policy instead of introducing a new named preset for this one tuning change.

### Checklist
- [x] Change the default `mostly-empty` reveal distribution to `80% empty / 15% single-cell / 5% full-room`.
- [x] Add a direct regression for the reveal-policy cutoffs.
- [x] Update the repo docs/task notes to stop claiming the old `90 / 8 / 2` split.

### Review
- Updated the live `mostly-empty` reveal policy thresholds in `stostone.generator.service` so generated puzzles now resolve to `empty` for rolls below `0.8`, `single-cell` up to `0.95`, and `full-room` after that.
- Added a focused regression that checks the exact cutoff behavior directly, so future generator changes cannot silently drift the reveal distribution.
- Updated the README to describe the new default reveal split.

### Commands Run
- `python -m pytest tests\test_generator.py` -> `11 passed in 4.83s`
- `python -m pytest` -> `58 passed in 6.98s`
