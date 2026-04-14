from __future__ import annotations

import json
import re
from pathlib import Path

from ..generator import build_puzzle
from ..models import Puzzle, PuzzleMetadata, PuzzleSpec, PuzzleSummary, metadata_from_legacy_dict


def _read_puzzle_info(file) -> str | None:
    info = file.read().strip()
    return info or None


def _parse_info_payload(info: str | None) -> dict[str, object]:
    if info is None:
        return {}

    info_text = info.strip()
    if info_text.startswith("info:"):
        info_text = info_text[5:].strip()

    if not info_text:
        return {}

    try:
        payload = json.loads(info_text)
    except json.JSONDecodeError:
        fields = dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', info_text))
        return {"metadata": fields} if fields else {}

    return payload if isinstance(payload, dict) else {}


def _extract_puzzle_metadata(info: str | None) -> PuzzleMetadata:
    metadata = _parse_info_payload(info).get("metadata")
    return metadata_from_legacy_dict(metadata if isinstance(metadata, dict) else None)


def _format_info_section(puzzle: Puzzle) -> str:
    payload = _parse_info_payload(puzzle.spec.info_section)
    payload["metadata"] = puzzle.spec.metadata.to_legacy_dict()
    return "info:" + json.dumps(payload, indent=1)


def _read_puzzle_sections(file) -> tuple[
    int,
    int,
    int,
    list[list[int]],
    list[tuple[tuple[int, int], int] | None],
    list[list[int | str]],
]:
    file.readline()
    file.readline()
    rows = int(file.readline())
    cols = int(file.readline())
    rooms = int(file.readline())

    layout = [[int(symbol) for symbol in file.readline().strip().split()] for _ in range(rows)]

    weights: list[tuple[tuple[int, int], int] | None] = [None] * rooms
    for row in range(rows):
        for col, weight in enumerate(file.readline().strip().split()):
            if weight != ".":
                weights[layout[row][col]] = ((row, col), int(weight))

    initial_state = [[-1 if cell == "." else " #" for cell in file.readline().strip().split()] for _ in range(rows)]
    return rows, cols, rooms, layout, weights, initial_state


def load_puzzle_summary(path: Path | str) -> PuzzleSummary:
    puzzle_path = Path(path).resolve()
    with open(puzzle_path, "r") as file:
        rows, cols, rooms, _, weights, initial_state = _read_puzzle_sections(file)
        info = _read_puzzle_info(file)
        metadata = _extract_puzzle_metadata(info)

    return PuzzleSummary(
        path=puzzle_path,
        rows=rows,
        cols=cols,
        rooms=rooms,
        numbered_rooms=sum(weight is not None for weight in weights),
        pre_shaded_cells=sum(cell == " #" for row in initial_state for cell in row),
        metadata=metadata,
    )


def load_puzzle(path: Path | str) -> Puzzle:
    puzzle_path = Path(path).resolve()
    with open(puzzle_path, "r") as file:
        rows, cols, rooms, layout, weights, initial_state = _read_puzzle_sections(file)
        info = _read_puzzle_info(file)
        metadata = _extract_puzzle_metadata(info)

    spec = PuzzleSpec(
        rows=rows,
        cols=cols,
        rooms=rooms,
        layout=layout,
        weights=weights,
        initial_state=initial_state,
        info_section=info,
        metadata=metadata,
    )
    puzzle = build_puzzle(spec, source_path=puzzle_path)

    for room_num, room_indices in enumerate(puzzle.cache.all_room_indices):
        initial_stones = {(r, c) for (r, c) in room_indices if puzzle.spec.initial_state[r][c] == " #"}
        if initial_stones:
            puzzle.cache.all_room_domains[room_num] = [
                subdomain for subdomain in puzzle.cache.all_room_domains[room_num] if initial_stones.issubset(subdomain)
            ]

    return puzzle


def write_puzpre(path: Path | str, puzzle: Puzzle) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def write_grid(file, rows: list[list[int | str]]) -> None:
        for row in rows:
            file.write(" ".join(str(cell) for cell in row) + "\n")

    with open(output_path, "w+", newline="\n") as file:
        file.write("pzprv3\nstostone\n")
        file.write(f"{puzzle.spec.rows}\n{puzzle.spec.cols}\n{puzzle.spec.rooms}\n")
        write_grid(file, puzzle.spec.layout)

        weight_lookup = {coord: weight for coord, weight in (value for value in puzzle.spec.weights if value is not None)}
        weight_rows = [
            [weight_lookup.get((r, c), ".") for c in range(puzzle.spec.cols)]
            for r in range(puzzle.spec.rows)
        ]
        write_grid(file, weight_rows)

        filled_cells = {coord for stone in puzzle.state.drawn_stones if stone is not None for coord in stone}
        stone_rows = [
            ["#" if (r, c) in filled_cells else "." for c in range(puzzle.spec.cols)]
            for r in range(puzzle.spec.rows)
        ]
        write_grid(file, stone_rows)

        file.write("\n" + _format_info_section(puzzle) + "\n")
