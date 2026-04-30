extends RefCounted
class_name ProgressStore

const SAVE_PATH: String = "user://player_progress.json"
const SCHEMA_VERSION: String = "1.0.0"

var data: Dictionary = {}


func _init() -> void:
	data = _default_data()


func load_progress() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		data = _default_data()
		return
	var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		data = _default_data()
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) == TYPE_DICTIONARY:
		data = parsed as Dictionary
	else:
		data = _default_data()
	if not data.has("completed_puzzles_by_id"):
		data = _default_data()


func save_progress() -> void:
	var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(data, "\t"))


func mark_completed(puzzle_id: String, elapsed_ms: int, hints_used: int) -> void:
	var completed: Dictionary = data["completed_puzzles_by_id"] as Dictionary
	var entry: Dictionary = completed.get(puzzle_id, {"best_time_ms": elapsed_ms, "completed_count": 0, "hints_used": hints_used}) as Dictionary
	if elapsed_ms < int(entry["best_time_ms"]):
		entry["best_time_ms"] = elapsed_ms
	entry["completed_count"] = int(entry["completed_count"]) + 1
	entry["hints_used"] = min(int(entry.get("hints_used", hints_used)), hints_used)
	completed[puzzle_id] = entry

	var wallet: Dictionary = data["prototype_wallet"] as Dictionary
	wallet["coins"] = int(wallet["coins"]) + 25
	wallet["lives"] = min(int(wallet["lives"]) + 1, 5)
	var unlocks: Dictionary = data["unlocks"] as Dictionary
	unlocks["classic_board"] = true
	save_progress()


func save_draft(draft: Dictionary) -> void:
	var drafts: Array = data.get("drafts", []) as Array
	drafts.append(draft)
	data["drafts"] = drafts
	save_progress()


func summary_text() -> String:
	var wallet: Dictionary = data["prototype_wallet"] as Dictionary
	var completed: Dictionary = data["completed_puzzles_by_id"] as Dictionary
	return "Prototype coins: %s | lives: %s | completed: %s" % [wallet["coins"], wallet["lives"], completed.size()]


func _default_data() -> Dictionary:
	return {
		"schema_version": SCHEMA_VERSION,
		"completed_puzzles_by_id": {},
		"prototype_wallet": {"lives": 5, "coins": 0},
		"unlocks": {"default_theme": true},
		"drafts": [],
		"notice": "Local MVP progress only. Lives, coins, unlocks, and drafts are not secure or authoritative."
	}
