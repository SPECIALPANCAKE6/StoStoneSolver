# StoStoneSolver

This repository began as my thesis project: a Python solver for the Sto-Stone puzzle and its Sto-Sand variant. I am revisiting it now as the solver foundation for a broader Sto-Stone project that should eventually include puzzle generation and simple playable desktop, browser, and mobile experiences.

Today, this repository is still solver-first. It already parses puzzle files, solves sample puzzles from the command line, and exports solved PUZ-PRE files, but it does not yet include a generator or a playable UI. The codebase now uses a module-based package layout centered on `src/stostone/` instead of the older flat root-module arrangement.

## Vision

The solver is the correctness engine for everything that comes next. Before a generator or game client can be trustworthy, the core project needs a solid implementation of puzzle parsing, room-domain search, and Sto-Stone / Sto-Sand rule validation.

The longer-term direction for this project is:

- a reliable solver core
- a puzzle generator built on the same rule set and data model
- a simple playable Sto-Stone experience for desktop, browser, and mobile
- later presentation polish, including possible theming, once the core puzzle workflow is stable

## Current Status

What exists today:

- PUZ-PRE v3 puzzle parsing from `puzzles/*.txt`
- command-line puzzle listing, inspection, and solving
- solve modes for `sto-stone`, `sto-sand`, and `both`
- optional solved-puzzle export via `--solutions-dir`
- optional CLI logging via `--log-file`
- a standard-library-only Python codebase targeting Python 3.14

What does not exist yet:

- a puzzle generator
- a playable desktop, browser, or mobile UI
- a formal automated test suite

## What Sto-Stone Is

Sto-Stone is a logic puzzle played on a grid divided into rooms.

- If a room has a number, that room must contain exactly that many shaded cells.
- Shaded cells chosen inside a room must be orthogonally connected.
- Shaded cells cannot touch across room boundaries.
- After placement, each room's shaded pattern falls downward as a rigid connected shape.
- A Sto-Stone solution is accepted only when the final fallen arrangement fills the bottom half of the board with no gaps.

Sto-Sand uses the same room and shading rules, but changes the fall behavior: cells fall individually like grains instead of moving as rigid room-shaped stones.

## Quick Start

Run the solver from the repository root. The current CLI surface is:

- `list`: list bundled puzzle files
- `show`: inspect puzzle metadata without solving
- `solve`: solve one or more puzzles and optionally export solved PUZ-PRE files

The available solve modes are:

- `sto-stone`
- `sto-sand`
- `both`

Example commands:

```bash
python Solver.py --help
python Solver.py list
python Solver.py show 000-000
python Solver.py solve 000-000 --solutions-dir solutions
```

Example successful solve output:

```text
Solving 000-000.txt in Sto-Stone mode
Solved 000-000.txt in 0:00:00.000689
Wrote solution file: C:\Users\xtrem\OneDrive\Documents\codecraft\StoStoneSolver\solutions\000-000-solved.txt
Summary: solved 1 of 1 puzzle(s)
```

For full solve options:

```bash
python Solver.py solve --help
```

## Puzzle Files and Outputs

This repo stores input puzzles as `puzzles/*.txt` in PUZ-PRE v3 format. At a high level, each file contains:

```text
pzprv3
stostone
<rows>
<cols>
<rooms>
<room layout grid>
<weight grid>
<initial shaded-state grid>
```

See `puzzles/000-000.txt` for a small concrete example. Some sample puzzle images are also stored under `puzzles/images/`.

When a puzzle is solved with `--solutions-dir`, the solver writes a new PUZ-PRE file such as `solutions/000-000-solved.txt`. Optional CLI logs can be written anywhere with `--log-file`; the repo already ignores `logs/` and `solutions/` in git.

## How the Solver Works

For builders, the main parser contract is now:

```python
stostone.load_puzzle(path) -> Puzzle
```

The active `Puzzle` model carries separate immutable puzzle data, derived room caches, and mutable solver state while preserving the existing low-level grid/list representations.

Compatibility wrappers for the older flat API still live under `stostone.compat`.

The returned puzzle dictionary currently carries the solver's working state and precomputed room data, including:

- `rows`, `cols`, `rooms`
- `layout`, `weights`
- `initialState`, `state`
- `allRoomIndices`, `allRoomBorders`, `allRoomDomains`
- `drawnStones`

The active solver flow is:

1. Parse a PUZ-PRE puzzle into a puzzle dictionary.
2. Precompute room indices, borders, and candidate connected subgrids.
3. Backtrack by selecting one valid connected region per room.
4. Reject assignments that violate room-local or cross-room constraints.
5. Validate the final board under Sto-Stone or Sto-Sand fall rules.

The core modules in the active path are:

- `Solver.py`: thin repo-root CLI entrypoint
- `src/stostone/cli.py`: argument parsing, command dispatch, and logging setup
- `src/stostone/io/`: PUZ-PRE parsing, metadata loading, and solved-file export
- `src/stostone/models.py`: dataclasses for puzzle spec, caches, state, and solve results
- `src/stostone/core/`: shared grid, connectivity, and domain helpers
- `src/stostone/solver/`: search, validation, and state operations
- `src/stostone/generator/`: generator-facing construction/reset seams
- `src/stostone/compat/`: wrappers for the older flat module API

## Repository Layout

```text
StoStoneSolver/
|-- Solver.py
|-- README.md
|-- pyproject.toml
|-- docs/
|-- puzzles/
|-- src/
|   `-- stostone/
|       |-- cli.py
|       |-- models.py
|       |-- compat/
|       |-- core/
|       |-- generator/
|       |-- io/
|       `-- solver/
|-- stostone/
|-- puzzles/
|-- tasks/
|-- tests/
`-- AGENTS.md
```

In practice:

- `docs/` contains architecture notes and archived legacy examples
- `puzzles/` contains bundled sample inputs
- `puzzles/images/` contains reference images for some puzzles
- `solutions/` holds exported solved puzzle files
- `logs/` is a convenient location for CLI log output
- `src/stostone/` contains the real package implementation
- `stostone/` is a lightweight shim so the package can be run from the repo without installing first
- `tasks/` contains working notes, review notes, and project lessons

## Roadmap

The order matters here: solver quality comes first, then generator work, then gameplay layers.

1. Finish the current refactor cleanup and harden solver correctness.
2. Add reproducible validation, broader smoke coverage, and a real automated test story.
3. Build puzzle-generation capabilities on top of the solver's rule engine and data model.
4. Design a simple playable Sto-Stone experience for browser, desktop, and mobile.
5. Explore presentation polish and optional theming after the core play loop is stable.

## Contributing / Developer Notes

- Prefer explicit puzzle data passed through puzzle dictionaries over module-global state.
- Keep changes surgical and compatibility-minded; this repo is being modernized, not redesigned from scratch.
- There is no formal automated test suite yet, so use smoke validation on known sample puzzles.
- Useful smoke commands:

```bash
python Solver.py show 000-000
python Solver.py solve 000-000 --solutions-dir solutions
```

- Project-specific workflow guidance lives in `AGENTS.md`.
- Ongoing task and review notes live in `tasks/`.
