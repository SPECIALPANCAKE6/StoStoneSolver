# StoStoneSolver

This repository began as my thesis project: a Python solver for the Sto-Stone puzzle and its Sto-Sand variant. I am revisiting it now as the solver foundation for a broader Sto-Stone project that should eventually include puzzle generation and simple playable desktop, browser, and mobile experiences.

Today, this repository is still solver-first. It already parses puzzle files, solves sample puzzles from the command line, exports solved PUZ-PRE files, and now includes a seeded generator path that can build small local corpora of uniquely solvable puzzles. The current generator is constructive and solution-first: it builds a valid witness placement, greedily carves redundant numbered-room clues, then proves uniqueness, scores the result, and applies batch filters. The codebase now uses a module-based package layout centered on `src/stostone/` instead of the older flat root-module arrangement.

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
- command-line puzzle listing, inspection, solving, generation, and calibration reporting
- batch corpus generation with seed ranges, duplicate detection, and optional JSON summary output
- solve modes for `sto-stone`, `sto-sand`, and `both`
- optional solved-puzzle export via `--solutions-dir`
- optional CLI logging via `--log-file`
- a clean engine API for app-facing `load`, `summarize`, `solve`, `count`, `generate`, and `generate_corpus` calls
- a seeded generator API with constructive solution-first generation, greedy numbered-room clue carving, uniqueness proof, quality scoring, preset filters, and calibration reporting
- a repo-owned pytest suite covering the current package layout
- a standard-library-only Python codebase targeting Python 3.14

What does not exist yet:

- a playable desktop, browser, or mobile UI

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
- `generate`: create one puzzle or a small corpus and write the results to disk
- `calibrate`: analyze generated corpus summaries and recommend preset bands
- `calibrate-corpus`: run a JSON corpus matrix plan and write one combined calibration report

The available solve modes are:

- `sto-stone`
- `sto-sand`
- `both`

Example commands:

```bash
python Solver.py --help
python Solver.py list
python Solver.py show 000-000.txt
python Solver.py solve 000-000.txt --solutions-dir solutions
python Solver.py generate --rows 4 --cols 4 --rooms 4 --seed 0
python Solver.py generate --rows 4 --cols 4 --rooms 4 --seed 0 --no-clue-carving
python Solver.py generate --rows 4 --cols 4 --rooms 4 --count 5 --seed-start 0 --out-dir puzzles/generated --summary-file artifacts/generation-summary.json
python Solver.py calibrate artifacts/generation-summary.json --report artifacts/calibration/report.md --json-report artifacts/calibration/report.json
python Solver.py calibrate-corpus --plan artifacts/calibration/plan.json --report artifacts/calibration/report.md --json-report artifacts/calibration/report.json
```

By default, generated puzzles are written into `puzzles/` with a `generated-` prefix, for example `puzzles/generated-4x4-4r-seed0.txt`.
By default, generation also runs a greedy clue-carving pass that removes redundant numbered-room clues while preserving uniqueness. Use `--no-clue-carving` if you want the fully numbered version for debugging or comparison.
Reveal selection is now driven by named policy maps. The default `mostly-empty` reveal policy map resolves to `empty` 80% of the time, `few-cells` 15% of the time, and `full-room` 5% of the time. The `few-cells` mode reveals between 1 and 4 pre-filled witness cells.
Named generator presets now sit on top of that surface:

- quality presets: `balanced`, `strict`
- difficulty presets: `easy`, `medium`, `hard`, `expert`
- clue profiles: `minimal`, `varied`, `guided`, `room-reveal`

Clue profiles choose a default reveal/clue style, while quality and difficulty presets contribute reusable filter bands. Difficulty presets are size-aware: `4x4-4r`, `6x6-6r`, and `8x8-8r` use calibrated square-family bands, while other parseable sizes use a deterministic heuristic based on board area, aspect ratio, and room count until they have corpus data. Difficulty scoring uses the stamped `solver-log-area-v2` model so larger boards keep solve-iteration separation instead of saturating early. Explicit `--min-*` / `--max-*` CLI filters still apply on top and tighten the preset if both are provided.

The corpus route supports quality filters and duplicate control, for example:

```bash
python Solver.py generate --count 10 --rows 6 --cols 6 --rooms 6 --seed-start 100 --max-seeds 200 --min-room-balance 0.50 --min-shape-compactness 0.55 --min-solve-iterations 40 --out-dir puzzles/generated
python Solver.py generate --rows 4 --cols 4 --rooms 4 --seed 1 --difficulty-preset easy --clue-profile guided
```

Calibration does not generate puzzles by itself. It reads one or more summary JSON files produced by `generate --summary-file`, dedupes by puzzle signature, reports metric percentiles by board family, and writes recommended quality/difficulty bands for review. Family-level hit rates use size-aware preset bands when available; the overall section still uses global bands so cross-size drift remains visible.

For repeatable calibration runs, use `calibrate-corpus` with a plan file. Paths inside the plan are resolved relative to the plan file, and completed summaries are skipped unless `--force` is supplied:

```json
{
  "defaults": {
    "max_attempts": 256,
    "reveal_policy": "mostly-empty",
    "out_dir": "{family}",
    "summary_file": "{family}-summary.json"
  },
  "families": [
    { "rows": 4, "cols": 4, "rooms": 4, "count": 200, "seed_start": 0, "max_seeds": 1000 },
    { "rows": 6, "cols": 6, "rooms": 6, "count": 100, "seed_start": 10000, "max_seeds": 1000 },
    { "rows": 8, "cols": 8, "rooms": 8, "count": 50, "seed_start": 30000, "max_seeds": 1000 },
    { "rows": 4, "cols": 6, "rooms": 6, "count": 200, "seed_start": 20000, "max_seeds": 2000 }
  ]
}
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

The generator also lives in Python API form:

```python
import stostone

result = stostone.generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0)
print(result.attempts, result.applied_reveal_policy, result.solution_count)
```

For future desktop/mobile callers, the package also exposes a thin engine surface:

```python
import stostone

summary = stostone.engine.summarize("puzzles/000-000.txt")
solve_result = stostone.engine.solve("puzzles/000-000.txt")
count_result = stostone.engine.count("puzzles/000-001.txt", limit=2)
generation = stostone.engine.generate(rows=4, cols=4, rooms=4, seed=0)
corpus = stostone.engine.generate_corpus(count=5, rows=4, cols=4, rooms=4, seed_start=0, out_dir="puzzles/generated")
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

The parser returns a `Puzzle` object with three main layers:

- `spec`: immutable puzzle inputs such as `rows`, `cols`, `rooms`, `layout`, `weights`, and `initial_state`
- `cache`: derived room data such as `all_room_indices`, `all_room_borders`, and `all_room_domains`
- `state`: mutable solver state such as the working grid, drawn stones, and constraint-check count

The active solver flow is:

1. Parse a PUZ-PRE puzzle into a `Puzzle`.
2. Precompute room indices, borders, and candidate connected subgrids.
3. Backtrack by selecting one valid connected region per room.
4. Reject assignments that violate room-local or cross-room constraints.
5. Validate the final board under Sto-Stone or Sto-Sand fall rules.

The core modules in the active path are:

- `Solver.py`: thin repo-root CLI entrypoint
- `src/stostone/cli.py`: argument parsing, command dispatch, and logging setup
- `src/stostone/engine.py`: thin app-facing API over load, summarize, solve, count, and generation services
- `src/stostone/io/`: PUZ-PRE parsing, metadata loading, and solved-file export
- `src/stostone/models.py`: dataclasses for puzzle spec, caches, state, and solve results
- `src/stostone/core/`: shared grid, connectivity, and domain helpers
- `src/stostone/solver/`: search, validation, and state operations
- `src/stostone/assembly/`: puzzle assembly and room-cache construction from parsed specs
- `src/stostone/generator/`: seeded single-puzzle and corpus generation using a constructive solution-first search, uniqueness proof, duplicate detection, quality filters, presets, and calibration reporting

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
|       |-- assembly/
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
- Keep changes surgical and package-oriented; this repo is being modernized, not redesigned from scratch.
- The repo has a formal pytest suite; use that first, then add smoke commands when validating CLI behavior or manual flows.
- Useful smoke commands:

```bash
python Solver.py show 000-000
python Solver.py solve 000-000 --solutions-dir solutions
python Solver.py generate --count 2 --rows 4 --cols 4 --rooms 4 --seed-start 0 --out-dir test-output/manual-corpus
python -m pytest
```

- Project-specific workflow guidance lives in `AGENTS.md`.
- Ongoing task and review notes live in `tasks/`.
