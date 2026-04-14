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
- `stostone.io`: PUZ-PRE parsing, metadata loading, and solved-file export.
- `stostone.core`: grid geometry, connectivity, and domain enumeration helpers.
- `stostone.solver`: state mutation, validation, search, and solve orchestration.
- `stostone.generator`: in-memory puzzle construction and reset seams for upcoming generator work.
- `stostone.compat`: compatibility wrappers for the old flat-module APIs, kept inside the package instead of the repo root.

## Entry Points

- `python Solver.py ...` remains the simple repo-root entrypoint.
- `python -m stostone.cli ...` runs the package-native CLI.

## Notes

- The root `stostone/` directory is a lightweight shim so the package can be run from the repo without an install step.
- Historical solved samples were moved to `docs/examples/legacy-solutions/` so the root stays focused on code and project metadata.
