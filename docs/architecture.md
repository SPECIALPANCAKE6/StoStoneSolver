# Architecture

## Layout

The repository now follows a module-based layout:

```text
StoStoneSolver/
|-- Solver.py
|-- README.md
|-- pyproject.toml
|-- docs/
|   |-- architecture.md
|   `-- examples/
|       `-- legacy-solutions/
|-- puzzles/
|-- src/
|   `-- stostone/
|       |-- cli.py
|       |-- models.py
|       |-- assembly/
|       |-- compat/
|       |-- core/
|       |-- generator/
|       |-- io/
|       `-- solver/
|-- stostone/
|-- tasks/
`-- tests/
```

## Package Responsibilities

- `stostone.models`: dataclasses for immutable puzzle data, derived caches, mutable state, and solve results.
- `stostone.engine`: app-facing orchestration layer for `load`, `summarize`, `solve`, `count`, `generate`, and `generate_corpus`.
- `stostone.io`: PUZ-PRE parsing, metadata loading, and solved-file export.
- `stostone.core`: grid geometry, connectivity, and domain enumeration helpers.
- `stostone.solver`: state mutation, validation, search, and solve orchestration.
- `stostone.assembly`: in-memory puzzle assembly and room-cache construction from parsed specs.
- `stostone.generator`: seeded single-puzzle and corpus generation using a constructive solution-first search, greedy numbered-room clue carving, uniqueness proof, duplicate detection, quality filters, size-aware presets, calibration reports, and plan-driven calibration corpus runs.
- `stostone.compat`: compatibility wrappers for the old flat-module APIs, kept inside the package instead of the repo root.

## Entry Points

- `python Solver.py ...` remains the simple repo-root entrypoint.
- `python -m stostone.cli ...` runs the package-native CLI.
- `stostone.engine` is the stable in-process boundary for future desktop/mobile callers that should not depend on CLI parsing or logging.

## Notes

- The root `stostone/` directory is a lightweight shim so the package can be run from the repo without an install step.
- Historical solved samples were moved to `docs/examples/legacy-solutions/` so the root stays focused on code and project metadata.
