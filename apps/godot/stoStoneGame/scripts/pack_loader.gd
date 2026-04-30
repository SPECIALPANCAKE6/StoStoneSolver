extends RefCounted
class_name PackLoader

const SUPPORTED_SCHEMA_MAJOR: int = 1

static func load_pack(path: String) -> Dictionary:
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"ok": false, "error": "Could not open pack: %s" % path}

	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		return {"ok": false, "error": "Pack JSON root must be an object."}

	var parsed_pack: Dictionary = parsed as Dictionary
	var error: String = validate_pack(parsed_pack)
	if error != "":
		return {"ok": false, "error": error}
	return {"ok": true, "pack": parsed_pack}


static func validate_pack(pack: Dictionary) -> String:
	for key: String in [
		"schema_version",
		"pack_id",
		"pack_type",
		"contains_solutions",
		"contains_debug_data",
		"manifest",
		"puzzles_by_id",
		"solutions_by_puzzle_id",
		"hint_plans_by_puzzle_id",
	]:
		if not pack.has(key):
			return "Pack is missing required field: %s" % key

	var version_parts: PackedStringArray = str(pack["schema_version"]).split(".")
	var major: int = int(version_parts[0])
	if major != SUPPORTED_SCHEMA_MAJOR:
		return "Unsupported pack schema major version: %s" % major

	if typeof(pack["puzzles_by_id"]) != TYPE_DICTIONARY:
		return "Pack field puzzles_by_id must be an object."
	if typeof(pack["solutions_by_puzzle_id"]) != TYPE_DICTIONARY:
		return "Pack field solutions_by_puzzle_id must be an object."
	if typeof(pack["hint_plans_by_puzzle_id"]) != TYPE_DICTIONARY:
		return "Pack field hint_plans_by_puzzle_id must be an object."

	var puzzles_by_id: Dictionary = pack["puzzles_by_id"] as Dictionary
	for puzzle_id: String in puzzles_by_id.keys():
		var puzzle_data: Variant = puzzles_by_id[puzzle_id]
		if typeof(puzzle_data) != TYPE_DICTIONARY:
			return "Puzzle %s must be an object." % puzzle_id
		var puzzle: Dictionary = puzzle_data as Dictionary
		for key: String in ["puzzle_id", "rows", "cols", "layout", "weights", "initial_state", "difficulty"]:
			if not puzzle.has(key):
				return "Puzzle %s is missing required field: %s" % [puzzle_id, key]
	return ""


static func sorted_puzzle_ids(pack: Dictionary) -> Array:
	var puzzles_by_id: Dictionary = pack["puzzles_by_id"] as Dictionary
	var ids: Array = puzzles_by_id.keys()
	ids.sort()
	return ids
