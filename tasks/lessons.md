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
