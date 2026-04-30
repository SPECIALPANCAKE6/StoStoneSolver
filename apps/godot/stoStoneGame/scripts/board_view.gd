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


func set_drop_preview(cells: Array, enabled: bool) -> void:
	preview_cells = {}
	for cell: Array in cells:
		preview_cells[_key(int(cell[0]), int(cell[1]))] = true
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
				draw_rect(rect.grow(-4), Color(0.49, 0.71, 0.95, 0.55), true)
			if shaded.has(key):
				draw_rect(rect.grow(-5), Color(0.15, 0.17, 0.2), true)
			if givens.has(key):
				draw_rect(rect.grow(-9), Color(0.05, 0.05, 0.06), true)
			if hint_cell.size() == 2 and int(hint_cell[0]) == row and int(hint_cell[1]) == col:
				draw_rect(rect.grow(-2), Color(0.98, 0.79, 0.25, 0.5), false, 4.0)
			if weights_by_cell.has(key):
				draw_string(font, rect.position + Vector2(8, 20), str(weights_by_cell[key]), HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color(0.1, 0.12, 0.14))
			draw_rect(rect, Color(0.72, 0.72, 0.68), false, 1.0)

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
		result[_key(int(cell[0]), int(cell[1]))] = weight["value"]
	return result


func _key(row: int, col: int) -> String:
	return "%s,%s" % [row, col]


func _room_at(layout: Array, row: int, col: int) -> int:
	var layout_row: Array = layout[row] as Array
	return int(layout_row[col])
