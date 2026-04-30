extends Control

const PACK_PATH: String = "res://assets/packs/starter_pack.json"

var pack: Dictionary = {}
var puzzle_ids: Array = []
var selected_puzzle_id: String = ""
var shaded: Dictionary = {}
var hint_index: int = 0
var started_at_ms: int = 0
var progress: ProgressStore = ProgressStore.new()

var puzzle_list: ItemList
var board: BoardView
var title_label: Label
var status_label: Label
var tutorial_label: Label
var progress_label: Label
var hint_button: Button
var preview_button: Button
var preview_enabled: bool = false


func _ready() -> void:
	progress.load_progress()
	_build_ui()
	_load_pack()


func _build_ui() -> void:
	var root: HBoxContainer = HBoxContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override("separation", 16)
	add_child(root)

	var sidebar: VBoxContainer = VBoxContainer.new()
	sidebar.custom_minimum_size = Vector2(310, 0)
	root.add_child(sidebar)

	title_label = Label.new()
	title_label.text = "StoStone"
	title_label.add_theme_font_size_override("font_size", 26)
	sidebar.add_child(title_label)

	progress_label = Label.new()
	progress_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sidebar.add_child(progress_label)

	puzzle_list = ItemList.new()
	puzzle_list.custom_minimum_size = Vector2(280, 420)
	puzzle_list.item_selected.connect(_on_puzzle_selected)
	sidebar.add_child(puzzle_list)

	var draft_button: Button = Button.new()
	draft_button.text = "New Local Draft"
	draft_button.pressed.connect(_save_local_draft)
	sidebar.add_child(draft_button)

	var content: VBoxContainer = VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(content)

	tutorial_label = Label.new()
	tutorial_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tutorial_label.custom_minimum_size = Vector2(0, 72)
	content.add_child(tutorial_label)

	board = BoardView.new()
	board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	board.size_flags_vertical = Control.SIZE_EXPAND_FILL
	board.cell_toggled.connect(_toggle_cell)
	content.add_child(board)

	var actions: HBoxContainer = HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	content.add_child(actions)

	var check_button: Button = Button.new()
	check_button.text = "Check"
	check_button.pressed.connect(_check_board)
	actions.add_child(check_button)

	hint_button = Button.new()
	hint_button.text = "Hint"
	hint_button.pressed.connect(_show_next_hint)
	actions.add_child(hint_button)

	preview_button = Button.new()
	preview_button.text = "Drop Preview"
	preview_button.pressed.connect(_toggle_drop_preview)
	actions.add_child(preview_button)

	var reset_button: Button = Button.new()
	reset_button.text = "Reset"
	reset_button.pressed.connect(_reset_current_puzzle)
	actions.add_child(reset_button)

	status_label = Label.new()
	status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status_label.custom_minimum_size = Vector2(0, 64)
	content.add_child(status_label)


func _load_pack() -> void:
	var loaded: Dictionary = PackLoader.load_pack(PACK_PATH)
	if not loaded["ok"]:
		status_label.text = str(loaded["error"])
		return
	pack = loaded["pack"] as Dictionary
	puzzle_ids = PackLoader.sorted_puzzle_ids(pack)
	puzzle_list.clear()
	var puzzles_by_id: Dictionary = pack["puzzles_by_id"] as Dictionary
	for puzzle_id: String in puzzle_ids:
		var puzzle: Dictionary = puzzles_by_id[puzzle_id] as Dictionary
		var difficulty: Dictionary = puzzle["difficulty"] as Dictionary
		var label: String = "%s  %s  %sx%s" % [puzzle.get("title", puzzle_id), difficulty["label"], puzzle["rows"], puzzle["cols"]]
		puzzle_list.add_item(label)
	progress_label.text = progress.summary_text()
	if puzzle_ids.size() > 0:
		puzzle_list.select(0)
		_select_puzzle(puzzle_ids[0])


func _on_puzzle_selected(index: int) -> void:
	_select_puzzle(str(puzzle_ids[index]))


func _select_puzzle(puzzle_id: String) -> void:
	selected_puzzle_id = puzzle_id
	var puzzles_by_id: Dictionary = pack["puzzles_by_id"] as Dictionary
	var puzzle: Dictionary = puzzles_by_id[puzzle_id] as Dictionary
	shaded = {}
	var initial_state: Array = puzzle.get("initial_state", []) as Array
	for cell: Array in initial_state:
		shaded[_key(int(cell[0]), int(cell[1]))] = true
	hint_index = 0
	preview_enabled = false
	started_at_ms = Time.get_ticks_msec()
	board.set_puzzle(puzzle, _shaded_array())
	_update_tutorial_text(puzzle)
	status_label.text = "Shade connected stones inside rooms. Use Check when the board looks solved."


func _update_tutorial_text(puzzle: Dictionary) -> void:
	var manifest: Dictionary = pack["manifest"] as Dictionary
	var pack_notice: String = str(manifest.get("solution_data_notice", ""))
	var text: String = "Local MVP pack. %s" % pack_notice
	if puzzle.has("tutorial"):
		var tutorial: Dictionary = puzzle["tutorial"] as Dictionary
		text = "%s\n%s" % [tutorial.get("message", ""), pack_notice]
	tutorial_label.text = text


func _toggle_cell(row: int, col: int) -> void:
	if selected_puzzle_id == "":
		return
	var puzzles_by_id: Dictionary = pack["puzzles_by_id"] as Dictionary
	var puzzle: Dictionary = puzzles_by_id[selected_puzzle_id] as Dictionary
	var key: String = _key(row, col)
	if _given_keys(puzzle).has(key):
		status_label.text = "That cell is a given and cannot be changed."
		return
	if shaded.has(key):
		shaded.erase(key)
	else:
		shaded[key] = true
	board.set_shaded_cells(_shaded_array())
	preview_enabled = false
	_update_drop_preview()


func _check_board() -> void:
	if selected_puzzle_id == "":
		return
	var feedback: Array[String] = _local_rule_feedback()
	if feedback.size() > 0:
		status_label.text = _join_lines(feedback)
		return
	if _is_complete():
		var elapsed: int = Time.get_ticks_msec() - started_at_ms
		progress.mark_completed(selected_puzzle_id, elapsed, hint_index)
		progress_label.text = progress.summary_text()
		status_label.text = "Solved in %.1f seconds. The drop preview shows the stones filling the bottom half." % (float(elapsed) / 1000.0)
		preview_enabled = true
		_update_drop_preview()
	else:
		status_label.text = "Local rules look okay so far, but this does not match the bundled MVP solution yet."


func _show_next_hint() -> void:
	if selected_puzzle_id == "":
		return
	var hint_plans_by_puzzle_id: Dictionary = pack["hint_plans_by_puzzle_id"] as Dictionary
	var hints: Array = hint_plans_by_puzzle_id.get(selected_puzzle_id, []) as Array
	if hints.is_empty():
		status_label.text = "No hints are available for this puzzle."
		return
	var hint: Dictionary = hints[min(hint_index, hints.size() - 1)] as Dictionary
	hint_index = min(hint_index + 1, hints.size())
	status_label.text = hint.get("message", "Try focusing on one numbered room.")
	if hint.has("cell"):
		board.set_hint_cell(hint["cell"])
	if hint.get("kind", "") == "drop_preview":
		preview_enabled = true
		_update_drop_preview()


func _toggle_drop_preview() -> void:
	preview_enabled = not preview_enabled
	_update_drop_preview()
	status_label.text = "Drop preview shows where the solved room-shapes land after rigid gravity." if preview_enabled else "Drop preview hidden."


func _update_drop_preview() -> void:
	if selected_puzzle_id == "":
		return
	var solutions_by_puzzle_id: Dictionary = pack["solutions_by_puzzle_id"] as Dictionary
	var solution: Dictionary = solutions_by_puzzle_id.get(selected_puzzle_id, {}) as Dictionary
	var cells: Array = []
	if solution.has("drop_preview"):
		var drop_preview: Dictionary = solution["drop_preview"] as Dictionary
		cells = drop_preview.get("final_filled_cells", []) as Array
	board.set_drop_preview(cells, preview_enabled)


func _reset_current_puzzle() -> void:
	if selected_puzzle_id != "":
		_select_puzzle(selected_puzzle_id)


func _save_local_draft() -> void:
	var draft: Dictionary = {
		"created_at_unix": Time.get_unix_time_from_system(),
		"rows": 4,
		"cols": 4,
		"layout": [[0, 0, 1, 1], [0, 0, 1, 1], [2, 2, 3, 3], [2, 2, 3, 3]],
		"weights": [],
		"initial_state": [],
		"status": "draft_only_unvalidated"
	}
	progress.save_draft(draft)
	progress_label.text = progress.summary_text()
	status_label.text = "Saved a local draft puzzle. Uniqueness validation is deferred to Python or a future service."


func _local_rule_feedback() -> Array[String]:
	var puzzles_by_id: Dictionary = pack["puzzles_by_id"] as Dictionary
	var puzzle: Dictionary = puzzles_by_id[selected_puzzle_id] as Dictionary
	var feedback: Array[String] = []
	var layout: Array = puzzle["layout"] as Array
	var room_counts: Dictionary = {}
	for key: String in shaded.keys():
		var parts: PackedStringArray = str(key).split(",")
		var row: int = int(parts[0])
		var col: int = int(parts[1])
		var room_id: int = _room_at(layout, row, col)
		room_counts[room_id] = int(room_counts.get(room_id, 0)) + 1
		for neighbor: Array in _neighbors(row, col, int(puzzle["rows"]), int(puzzle["cols"])):
			var n_key: String = _key(neighbor[0], neighbor[1])
			if shaded.has(n_key) and _room_at(layout, int(neighbor[0]), int(neighbor[1])) != room_id:
				feedback.append("Shaded cells touch across a room border at [%s, %s]." % [row, col])
				return feedback

	var weights: Array = puzzle.get("weights", []) as Array
	for weight: Dictionary in weights:
		var room_id: int = int(weight["room_id"])
		var expected: int = int(weight["value"])
		var actual: int = int(room_counts.get(room_id, 0))
		if actual > expected:
			feedback.append("Room %s has too many shaded cells: %s/%s." % [room_id + 1, actual, expected])
		elif actual < expected:
			feedback.append("Room %s still needs shaded cells: %s/%s." % [room_id + 1, actual, expected])

	for room_id: int in room_counts.keys():
		if not _room_shaded_cells_connected(int(room_id), puzzle):
			feedback.append("Room %s shaded cells are not connected." % [int(room_id) + 1])
			break
	return feedback


func _room_shaded_cells_connected(room_id: int, puzzle: Dictionary) -> bool:
	var layout: Array = puzzle["layout"] as Array
	var cells: Array = []
	for key: String in shaded.keys():
		var parts: PackedStringArray = str(key).split(",")
		var row: int = int(parts[0])
		var col: int = int(parts[1])
		if _room_at(layout, row, col) == room_id:
			cells.append([row, col])
	if cells.size() <= 1:
		return true
	var target: Dictionary = {}
	for cell: Array in cells:
		target[_key(cell[0], cell[1])] = true
	var seen: Dictionary = {}
	var queue: Array = [cells[0]]
	var first_cell: Array = cells[0] as Array
	seen[_key(first_cell[0], first_cell[1])] = true
	while not queue.is_empty():
		var current: Array = queue.pop_front()
		for neighbor: Array in _neighbors(current[0], current[1], int(puzzle["rows"]), int(puzzle["cols"])):
			var key: String = _key(neighbor[0], neighbor[1])
			if target.has(key) and not seen.has(key):
				seen[key] = true
				queue.append(neighbor)
	return seen.size() == target.size()


func _is_complete() -> bool:
	var solutions_by_puzzle_id: Dictionary = pack["solutions_by_puzzle_id"] as Dictionary
	if not solutions_by_puzzle_id.has(selected_puzzle_id):
		return false
	var solution: Dictionary = solutions_by_puzzle_id[selected_puzzle_id] as Dictionary
	var solution_cells: Array = solution["shaded_cells"] as Array
	return _normalized_key_set(_shaded_array()) == _normalized_key_set(solution_cells)


func _normalized_key_set(cells: Array) -> Dictionary:
	var result: Dictionary = {}
	for cell: Array in cells:
		result[_key(int(cell[0]), int(cell[1]))] = true
	return result


func _shaded_array() -> Array:
	var cells: Array = []
	for key: String in shaded.keys():
		var parts: PackedStringArray = str(key).split(",")
		cells.append([int(parts[0]), int(parts[1])])
	cells.sort()
	return cells


func _given_keys(puzzle: Dictionary) -> Dictionary:
	var result: Dictionary = {}
	var initial_state: Array = puzzle.get("initial_state", []) as Array
	for cell: Array in initial_state:
		result[_key(int(cell[0]), int(cell[1]))] = true
	return result


func _neighbors(row: int, col: int, rows: int, cols: int) -> Array:
	var result: Array = []
	if row > 0:
		result.append([row - 1, col])
	if row + 1 < rows:
		result.append([row + 1, col])
	if col > 0:
		result.append([row, col - 1])
	if col + 1 < cols:
		result.append([row, col + 1])
	return result


func _key(row: int, col: int) -> String:
	return "%s,%s" % [row, col]


func _room_at(layout: Array, row: int, col: int) -> int:
	var layout_row: Array = layout[row] as Array
	return int(layout_row[col])


func _join_lines(lines: Array[String]) -> String:
	var text: String = ""
	for index: int in range(lines.size()):
		if index > 0:
			text += "\n"
		text += lines[index]
	return text
