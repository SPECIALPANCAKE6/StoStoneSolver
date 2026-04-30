extends Control
class_name BoardView

signal cell_toggled(row: int, col: int)

var puzzle: Dictionary = {}
var shaded: Dictionary = {}
var givens: Dictionary = {}
var hint_cell: Array = []
var preview_cells: Dictionary = {}
var show_preview: bool = false
var cell_size: float = 44.0


func set_puzzle(next_puzzle: Dictionary, shaded_cells: Array) -> void:
	puzzle = next_puzzle
	givens = {}
	var initial_state: Array = puzzle.get("initial_state", []) as Array
	for cell: Array in initial_state:
		givens[_key(int(cell[0]), int(cell[1]))] = true
	set_shaded_cells(shaded_cells)
	hint_cell = []
	preview_cells = {}
	show_preview = false
	queue_redraw()


func set_shaded_cells(cells: Array) -> void:
	shaded = {}
	for cell: Array in cells:
		shaded[_key(int(cell[0]), int(cell[1]))] = true
	queue_redraw()


func set_hint_cell(cell: Variant) -> void:
	if typeof(cell) == TYPE_ARRAY:
		hint_cell = cell as Array
	else:
		hint_cell = []
	queue_redraw()


func set_drop_preview(cells_by_room_id: Dictionary, enabled: bool) -> void:
	preview_cells = {}
	for room_id: int in cells_by_room_id.keys():
		var cells: Array = cells_by_room_id[room_id] as Array
		for cell: Array in cells:
			preview_cells[_key(int(cell[0]), int(cell[1]))] = room_id
	show_preview = enabled
	queue_redraw()


func _ready() -> void:
	custom_minimum_size = Vector2(520, 520)


func _gui_input(event: InputEvent) -> void:
	if puzzle.is_empty():
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var mouse_event: InputEventMouseButton = event as InputEventMouseButton
		var row: int = int(floor(mouse_event.position.y / cell_size))
		var col: int = int(floor(mouse_event.position.x / cell_size))
		if row >= 0 and row < int(puzzle["rows"]) and col >= 0 and col < int(puzzle["cols"]):
			cell_toggled.emit(row, col)


func _draw() -> void:
	if puzzle.is_empty():
		return

	var rows: int = int(puzzle["rows"])
	var cols: int = int(puzzle["cols"])
	cell_size = min(size.x / max(cols, 1), size.y / max(rows, 1))
	var board_size: Vector2 = Vector2(cols * cell_size, rows * cell_size)
	draw_rect(Rect2(Vector2.ZERO, board_size), Color(0.95, 0.94, 0.9), true)

	var font: Font = get_theme_default_font()
	var font_size: int = 16
	var layout: Array = puzzle["layout"] as Array
	var weights_by_cell: Dictionary = _weights_by_cell()
	for row: int in range(rows):
		for col: int in range(cols):
			var rect: Rect2 = Rect2(Vector2(col * cell_size, row * cell_size), Vector2(cell_size, cell_size))
			var key: String = _key(row, col)
			if show_preview and preview_cells.has(key):
				draw_rect(rect.grow(-4), _room_color(int(preview_cells[key]), 0.5), true)
			if shaded.has(key):
				var shaded_color: Color = _room_color(_room_at(layout, row, col), 0.9) if show_preview else Color(0.15, 0.17, 0.2)
				draw_rect(rect.grow(-5), shaded_color, true)
			if givens.has(key):
				draw_rect(rect.grow(-9), Color(0.05, 0.05, 0.06), true)
			if hint_cell.size() == 2 and int(hint_cell[0]) == row and int(hint_cell[1]) == col:
				draw_rect(rect.grow(-2), Color(0.98, 0.79, 0.25, 0.5), false, 4.0)
			if weights_by_cell.has(key):
				draw_string(font, rect.position + Vector2(8, 20), str(weights_by_cell[key]), HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color(0.1, 0.12, 0.14))
			draw_rect(rect, Color(0.72, 0.72, 0.68), false, 1.0)

	if show_preview:
		_draw_drop_guides(layout)

	for row: int in range(rows):
		for col: int in range(cols):
			var room_id: int = _room_at(layout, row, col)
			var origin: Vector2 = Vector2(col * cell_size, row * cell_size)
			if row == 0 or _room_at(layout, row - 1, col) != room_id:
				draw_line(origin, origin + Vector2(cell_size, 0), Color(0.06, 0.07, 0.09), 3.0)
			if col == 0 or _room_at(layout, row, col - 1) != room_id:
				draw_line(origin, origin + Vector2(0, cell_size), Color(0.06, 0.07, 0.09), 3.0)
			if row == rows - 1 or _room_at(layout, row + 1, col) != room_id:
				draw_line(origin + Vector2(0, cell_size), origin + Vector2(cell_size, cell_size), Color(0.06, 0.07, 0.09), 3.0)
			if col == cols - 1 or _room_at(layout, row, col + 1) != room_id:
				draw_line(origin + Vector2(cell_size, 0), origin + Vector2(cell_size, cell_size), Color(0.06, 0.07, 0.09), 3.0)


func _weights_by_cell() -> Dictionary:
	var result: Dictionary = {}
	var weights: Array = puzzle.get("weights", []) as Array
	for weight: Dictionary in weights:
		var cell: Array = weight["cell"] as Array
		result[_key(int(cell[0]), int(cell[1]))] = weight["value"] as int
	return result


func _key(row: int, col: int) -> String:
	return "%s,%s" % [row, col]


func _room_at(layout: Array, row: int, col: int) -> int:
	var layout_row: Array = layout[row] as Array
	return int(layout_row[col])


func _draw_drop_guides(layout: Array) -> void:
	var offsets_by_room_id: Dictionary = _preview_offsets_by_room_id(layout)
	for key: String in shaded.keys():
		var parts: PackedStringArray = key.split(",")
		var row: int = int(parts[0])
		var col: int = int(parts[1])
		var room_id: int = _room_at(layout, row, col)
		var offset: int = int(offsets_by_room_id.get(room_id, 0))
		if offset <= 0:
			continue
		var destination_key: String = _key(row + offset, col)
		if not preview_cells.has(destination_key) or int(preview_cells[destination_key]) != room_id:
			continue
		var source_center: Vector2 = Vector2((float(col) + 0.5) * cell_size, (float(row) + 0.5) * cell_size)
		var destination_center: Vector2 = Vector2((float(col) + 0.5) * cell_size, (float(row + offset) + 0.5) * cell_size)
		var guide_color: Color = _room_color(room_id, 0.58)
		draw_line(source_center, destination_center, guide_color, 3.0)
		var arrow_tip: Vector2 = destination_center + Vector2(0, min(8.0, cell_size * 0.18))
		var arrow_left: Vector2 = arrow_tip + Vector2(-min(6.0, cell_size * 0.14), -min(9.0, cell_size * 0.2))
		var arrow_right: Vector2 = arrow_tip + Vector2(min(6.0, cell_size * 0.14), -min(9.0, cell_size * 0.2))
		var arrow_points: PackedVector2Array = PackedVector2Array([arrow_tip, arrow_left, arrow_right])
		var arrow_colors: PackedColorArray = PackedColorArray([guide_color, guide_color, guide_color])
		draw_polygon(arrow_points, arrow_colors)


func _preview_offsets_by_room_id(layout: Array) -> Dictionary:
	var source_min_by_room_id: Dictionary = {}
	for key: String in shaded.keys():
		var parts: PackedStringArray = key.split(",")
		var row: int = int(parts[0])
		var col: int = int(parts[1])
		var room_id: int = _room_at(layout, row, col)
		var current_min: int = int(source_min_by_room_id.get(room_id, row))
		source_min_by_room_id[room_id] = min(current_min, row)

	var landing_min_by_room_id: Dictionary = {}
	for key: String in preview_cells.keys():
		var parts: PackedStringArray = key.split(",")
		var row: int = int(parts[0])
		var room_id: int = int(preview_cells[key])
		var current_min: int = int(landing_min_by_room_id.get(room_id, row))
		landing_min_by_room_id[room_id] = min(current_min, row)

	var offsets_by_room_id: Dictionary = {}
	for room_id: int in source_min_by_room_id.keys():
		if landing_min_by_room_id.has(room_id):
			offsets_by_room_id[room_id] = int(landing_min_by_room_id[room_id]) - int(source_min_by_room_id[room_id])
	return offsets_by_room_id


func _room_color(room_id: int, alpha: float) -> Color:
	var palette: Array[Color] = [
		Color(0.86, 0.25, 0.21, alpha),
		Color(0.13, 0.55, 0.93, alpha),
		Color(0.14, 0.62, 0.35, alpha),
		Color(0.94, 0.66, 0.12, alpha),
		Color(0.55, 0.32, 0.86, alpha),
		Color(0.06, 0.63, 0.65, alpha),
		Color(0.91, 0.33, 0.61, alpha),
		Color(0.38, 0.47, 0.12, alpha),
	]
	return palette[room_id % palette.size()]
