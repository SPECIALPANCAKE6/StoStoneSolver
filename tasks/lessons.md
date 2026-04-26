# Lessons

- When a room domain is filtered to include pre-shaded givens, backtracking cleanup cannot blindly reset those cells to `-1`; it must restore from `initialState` on branch unwind.
- Sto-Stone rigid-drop checks must validate every destination cell except self-overlap cells. Treating a drop as valid when only one destination cell is empty is incorrect.
- Sto-Stone acceptance cannot stop at per-column counts after the rigid drop. The final board must be exactly the contiguous bottom half of the grid, with no gaps above it.
- In the rigid-drop simulation, droppability cannot be cached across passes. A stone that was blocked can become movable after another stone falls, so the solver must recompute downward moves from the current board state each pass.
- `domainGen.py` is not part of the live solver path. Any future revival should start from the room-domain loop in `readPuzzle.py`, not from the current stale prototype.
- Lightweight CLI metadata commands should stay on a parse-only path. Building room domains and mutable solver state just to show puzzle counts adds unnecessary work and couples inspection to solver internals.
- If a legacy helper module must remain for compatibility, point it at the shared live implementation instead of carrying a second stale algorithm that can drift.
- Keep package `__init__` files lightweight during a module split. Pulling in high-level orchestration imports from `__init__` can create circular imports between generator, IO, and solver layers before the package finishes initializing.
- If the goal is a visibly cleaner architecture, moving implementation into packages is not enough by itself. The repo root should only keep true entrypoints and project metadata; legacy surfaces belong under an explicit `compat` package, not as top-level files.
- In this workspace, pytest's default temp/cache directories are unreliable on Windows/OneDrive. Prefer a repo-owned writable fixture directory for test outputs and disable cacheprovider if it causes permission noise.
- Windows subprocess-based CLI tests can fail under pytest with `WinError 6` unless stdin is detached. Use `stdin=subprocess.DEVNULL` in the test harness.
- A Sto-Stone uniqueness-count path cannot reuse successful leaf validation naively. `is_sto_stone(...)` leaves the dropped final board in place on success, so bounded multi-solution search must snapshot and restore the grid around successful Sto-Stone checks.
- For numbered-room generation, forcing room weights to sum to exactly half the board area dramatically improves candidate filtering. Any other total can never satisfy the final Sto-Stone bottom-half fill condition, so it is wasted search.
- When cloning a `Puzzle` through its legacy-dict surface, deep-copy the nested grids, domains, and drawn-stone lists first. Reusing those mutable references leaks solver-state mutations back into the original puzzle and can invalidate later uniqueness or duplicate checks.
- For unsolved generated puzzles, `write_puzpre(...)` cannot rely only on `state.drawn_stones`. If there is no solved state yet, it must fall back to `spec.initial_state` so pre-shaded givens survive round-trip.
- In generator metadata, `pre_solved_rooms` tracks fully revealed witness stones from the reveal policy, not rooms whose entire geometric area is pre-shaded.
