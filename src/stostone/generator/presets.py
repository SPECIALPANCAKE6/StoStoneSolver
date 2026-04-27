from __future__ import annotations

import math
import re
from dataclasses import dataclass

from ..models import GenerationFilters

QUALITY_PRESETS: dict[str, GenerationFilters] = {
    "balanced": GenerationFilters(min_room_balance=0.3, min_shape_compactness=0.75, max_room_size_spread=5),
    "strict": GenerationFilters(min_room_balance=0.4, min_shape_compactness=0.85, max_room_size_spread=4),
}

DIFFICULTY_PRESETS: dict[str, GenerationFilters] = {
    "easy": GenerationFilters(max_difficulty_score=25.0),
    "medium": GenerationFilters(min_difficulty_score=25.0, max_difficulty_score=50.0),
    "hard": GenerationFilters(min_difficulty_score=50.0, max_difficulty_score=75.0),
    "expert": GenerationFilters(min_difficulty_score=75.0),
}

SIZE_AWARE_DIFFICULTY_PRESETS: dict[str, dict[str, GenerationFilters]] = {
    "4x4-4r": {
        "easy": GenerationFilters(max_difficulty_score=40.0),
        "medium": GenerationFilters(min_difficulty_score=40.0, max_difficulty_score=60.0),
        "hard": GenerationFilters(min_difficulty_score=60.0, max_difficulty_score=75.0),
        "expert": GenerationFilters(min_difficulty_score=75.0),
    },
    "6x6-6r": {
        "easy": GenerationFilters(max_difficulty_score=75.0),
        "medium": GenerationFilters(min_difficulty_score=75.0, max_difficulty_score=80.0),
        "hard": GenerationFilters(min_difficulty_score=80.0, max_difficulty_score=85.0),
        "expert": GenerationFilters(min_difficulty_score=85.0),
    },
    "8x8-8r": {
        "easy": GenerationFilters(max_difficulty_score=50.0),
        "medium": GenerationFilters(min_difficulty_score=50.0, max_difficulty_score=80.0),
        "hard": GenerationFilters(min_difficulty_score=80.0, max_difficulty_score=90.0),
        "expert": GenerationFilters(min_difficulty_score=90.0),
    },
}


@dataclass(slots=True, frozen=True)
class ClueProfilePreset:
    reveal_policy: str
    clue_carving: bool = True
    max_given_shaded_cells: int | None = None
    max_pre_solved_rooms: int | None = None

    def to_filters(self) -> GenerationFilters:
        return GenerationFilters(
            max_given_shaded_cells=self.max_given_shaded_cells,
            max_pre_solved_rooms=self.max_pre_solved_rooms,
        )


CLUE_PROFILES: dict[str, ClueProfilePreset] = {
    "minimal": ClueProfilePreset(reveal_policy="empty", clue_carving=True, max_given_shaded_cells=0, max_pre_solved_rooms=0),
    "varied": ClueProfilePreset(reveal_policy="mostly-empty", clue_carving=True, max_given_shaded_cells=4, max_pre_solved_rooms=1),
    "guided": ClueProfilePreset(reveal_policy="few-cells", clue_carving=True, max_given_shaded_cells=4, max_pre_solved_rooms=2),
    "room-reveal": ClueProfilePreset(reveal_policy="full-room", clue_carving=True, max_pre_solved_rooms=1),
}


def board_family_key(rows: int, cols: int, rooms: int) -> str:
    return f"{rows}x{cols}-{rooms}r"


def _parse_board_family(board_family: str | None) -> tuple[int, int, int] | None:
    if board_family is None:
        return None
    match = re.fullmatch(r"(?P<rows>\d+)x(?P<cols>\d+)-(?P<rooms>\d+)r", board_family)
    if match is None:
        return None
    return int(match.group("rows")), int(match.group("cols")), int(match.group("rooms"))


def _round_cutoff(value: float) -> float:
    return float(math.floor((value / 5.0) + 0.5) * 5)


def _interpolate_cutoffs(area: int) -> tuple[float, float, float]:
    anchors = (
        (16, (40.0, 60.0, 75.0)),
        (36, (75.0, 80.0, 85.0)),
        (64, (50.0, 80.0, 90.0)),
    )
    if area <= anchors[0][0]:
        return anchors[0][1]

    for index, (anchor_area, anchor_cutoffs) in enumerate(anchors[1:], start=1):
        previous_area, previous_cutoffs = anchors[index - 1]
        if area <= anchor_area:
            ratio = (area - previous_area) / (anchor_area - previous_area)
            return tuple(
                previous + ((current - previous) * ratio)
                for previous, current in zip(previous_cutoffs, anchor_cutoffs)
            )

    growth = math.log2(area / anchors[-1][0])
    easy, medium, hard = anchors[-1][1]
    return min(85.0, easy + (growth * 5.0)), min(92.0, medium + (growth * 3.0)), min(97.0, hard + (growth * 2.0))


def _heuristic_difficulty_presets(rows: int, cols: int, rooms: int) -> dict[str, GenerationFilters]:
    area = rows * cols
    easy_max, medium_max, hard_max = _interpolate_cutoffs(area)
    aspect_ratio = max(rows, cols) / max(1, min(rows, cols))
    aspect_adjustment = min(5.0, max(0.0, aspect_ratio - 1.0) * 10.0)
    default_rooms = max(1, min(cols, area // 2))
    room_adjustment = max(-5.0, min(5.0, ((rooms / default_rooms) - 1.0) * 5.0))

    easy_max = _round_cutoff(min(90.0, easy_max + aspect_adjustment + room_adjustment))
    medium_max = _round_cutoff(min(95.0, medium_max + aspect_adjustment + room_adjustment))
    hard_max = _round_cutoff(min(98.0, hard_max + aspect_adjustment + room_adjustment))
    medium_max = min(95.0, max(easy_max + 5.0, medium_max))
    hard_max = min(98.0, max(medium_max + 5.0, hard_max))

    return {
        "easy": GenerationFilters(max_difficulty_score=easy_max),
        "medium": GenerationFilters(min_difficulty_score=easy_max, max_difficulty_score=medium_max),
        "hard": GenerationFilters(min_difficulty_score=medium_max, max_difficulty_score=hard_max),
        "expert": GenerationFilters(min_difficulty_score=hard_max),
    }


def difficulty_presets_for_family(board_family: str | None) -> dict[str, GenerationFilters]:
    if board_family is None:
        return DIFFICULTY_PRESETS
    if board_family in SIZE_AWARE_DIFFICULTY_PRESETS:
        return SIZE_AWARE_DIFFICULTY_PRESETS[board_family]
    parsed = _parse_board_family(board_family)
    if parsed is None:
        return DIFFICULTY_PRESETS
    return _heuristic_difficulty_presets(*parsed)


def difficulty_filter_for_preset(preset_name: str, board_family: str | None = None) -> GenerationFilters:
    return difficulty_presets_for_family(board_family)[preset_name]


def has_size_aware_difficulty(board_family: str | None) -> bool:
    return difficulty_scale_for_family(board_family) != "global"


def difficulty_scale_for_family(board_family: str | None) -> str:
    if board_family in SIZE_AWARE_DIFFICULTY_PRESETS:
        return "calibrated"
    if _parse_board_family(board_family) is not None:
        return "heuristic"
    return "global"


def _difficulty_filter_matches_score(score: float, filters: GenerationFilters) -> bool:
    if filters.min_difficulty_score is not None and score < filters.min_difficulty_score:
        return False
    if filters.max_difficulty_score is not None and score > filters.max_difficulty_score:
        return False
    return True


def difficulty_label_from_score(score: float, board_family: str | None = None) -> str:
    labels = {
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
        "expert": "Expert",
    }
    for preset_name in ("easy", "medium", "hard", "expert"):
        if _difficulty_filter_matches_score(score, difficulty_filter_for_preset(preset_name, board_family)):
            return labels[preset_name]
    return "Expert"


def merge_generation_filters(*filters: GenerationFilters | None) -> GenerationFilters:
    merged = GenerationFilters()
    for current in filters:
        if current is None:
            continue
        if current.min_room_balance is not None:
            merged.min_room_balance = current.min_room_balance if merged.min_room_balance is None else max(merged.min_room_balance, current.min_room_balance)
        if current.min_shape_compactness is not None:
            merged.min_shape_compactness = (
                current.min_shape_compactness
                if merged.min_shape_compactness is None
                else max(merged.min_shape_compactness, current.min_shape_compactness)
            )
        if current.max_room_size_spread is not None:
            merged.max_room_size_spread = (
                current.max_room_size_spread
                if merged.max_room_size_spread is None
                else min(merged.max_room_size_spread, current.max_room_size_spread)
            )
        if current.max_given_shaded_cells is not None:
            merged.max_given_shaded_cells = (
                current.max_given_shaded_cells
                if merged.max_given_shaded_cells is None
                else min(merged.max_given_shaded_cells, current.max_given_shaded_cells)
            )
        if current.max_pre_solved_rooms is not None:
            merged.max_pre_solved_rooms = (
                current.max_pre_solved_rooms
                if merged.max_pre_solved_rooms is None
                else min(merged.max_pre_solved_rooms, current.max_pre_solved_rooms)
            )
        if current.min_solve_iterations is not None:
            merged.min_solve_iterations = (
                current.min_solve_iterations
                if merged.min_solve_iterations is None
                else max(merged.min_solve_iterations, current.min_solve_iterations)
            )
        if current.max_solve_iterations is not None:
            merged.max_solve_iterations = (
                current.max_solve_iterations
                if merged.max_solve_iterations is None
                else min(merged.max_solve_iterations, current.max_solve_iterations)
            )
        if current.min_difficulty_score is not None:
            merged.min_difficulty_score = (
                current.min_difficulty_score
                if merged.min_difficulty_score is None
                else max(merged.min_difficulty_score, current.min_difficulty_score)
            )
        if current.max_difficulty_score is not None:
            merged.max_difficulty_score = (
                current.max_difficulty_score
                if merged.max_difficulty_score is None
                else min(merged.max_difficulty_score, current.max_difficulty_score)
            )
    return merged


def resolve_generation_controls(
    *,
    reveal_policy: str,
    clue_carving: bool,
    filters: GenerationFilters | None = None,
    quality_preset: str | None = None,
    difficulty_preset: str | None = None,
    clue_profile: str | None = None,
    board_family: str | None = None,
) -> tuple[GenerationFilters, str, bool]:
    if quality_preset is not None and quality_preset not in QUALITY_PRESETS:
        raise ValueError(f"Unsupported quality preset: {quality_preset}")
    if difficulty_preset is not None and difficulty_preset not in DIFFICULTY_PRESETS:
        raise ValueError(f"Unsupported difficulty preset: {difficulty_preset}")
    if clue_profile is not None and clue_profile not in CLUE_PROFILES:
        raise ValueError(f"Unsupported clue profile: {clue_profile}")

    clue_profile_preset = None if clue_profile is None else CLUE_PROFILES[clue_profile]
    resolved_filters = merge_generation_filters(
        None if quality_preset is None else QUALITY_PRESETS[quality_preset],
        None if difficulty_preset is None else difficulty_filter_for_preset(difficulty_preset, board_family),
        None if clue_profile_preset is None else clue_profile_preset.to_filters(),
        filters,
    )
    resolved_reveal_policy = reveal_policy if clue_profile_preset is None or reveal_policy != "mostly-empty" else clue_profile_preset.reveal_policy
    resolved_clue_carving = clue_carving if clue_profile_preset is None or not clue_carving else clue_profile_preset.clue_carving
    return resolved_filters, resolved_reveal_policy, resolved_clue_carving


__all__ = [
    "CLUE_PROFILES",
    "ClueProfilePreset",
    "DIFFICULTY_PRESETS",
    "QUALITY_PRESETS",
    "SIZE_AWARE_DIFFICULTY_PRESETS",
    "board_family_key",
    "difficulty_filter_for_preset",
    "difficulty_label_from_score",
    "difficulty_presets_for_family",
    "difficulty_scale_for_family",
    "has_size_aware_difficulty",
    "merge_generation_filters",
    "resolve_generation_controls",
]
