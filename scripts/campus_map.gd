class_name CampusMap
extends Control

var geography: Dictionary
var player_at := Vector2.ZERO
var heading := 0.0
var zoom := 0.0
var expanded := false
var marker := Vector2(-26, 23)
var message := ""
var view_origin := Vector2.ZERO
var view_factor := 1.0


func _draw() -> void:
	if geography.is_empty():
		return
	draw_rect(Rect2(Vector2.ZERO, size), Color("#111e20"))
	var inset := Vector2(22, 24)
	var map_size := size - inset * 2
	var view := Rect2(-180, -360, 680, 560) if expanded else Rect2(player_at - Vector2(93, 77), Vector2(186, 154))
	if zoom > 0.0:
		var focus := view.get_center()
		view.size /= 1.0 + zoom
		view.position = focus - view.size / 2
	view_factor = minf(map_size.x / view.size.x, map_size.y / view.size.y)
	view_origin = (size - view.size * view_factor) * .5 - view.position * view_factor
	var boundary := polygon(geography.boundary)
	if boundary.size() >= 3:
		draw_colored_polygon(boundary, Color("#213632"))
		boundary.append(boundary[0])
		draw_polyline(boundary, Color("#49756b"), 1.3, true)
	for green in geography.greens:
		var outline := polygon(green.points)
		if outline.size() >= 3:
			draw_colored_polygon(outline, Color("#365641"))
	for route in geography.roads:
		var line := polygon(route.points)
		if line.size() > 1:
			var fade := Color("#77928b") if route.type not in CampusSite.FOOTWAYS else Color("#435b58")
			draw_polyline(line, fade, maxf(1.0, route.width * view_factor), true)
	for entry in geography.buildings:
		var form := polygon(entry.footprint)
		if form.size() > 2:
			draw_colored_polygon(form, Color("#eeb786") if not entry.asset.is_empty() else Color("#516361"))
		if expanded and entry.id in ["osm-way-552610255", "osm-way-733313948", "osm-way-524812098",
				"osm-way-734918595", "osm-way-772103594", "osm-way-606238583"]:
			var names := {"osm-way-733313948": "MJIIT", "osm-way-734918595": "UTM KL Library"}
			var title: String = names.get(entry.id, entry.name)
			draw_string(get_theme_default_font(), screen(Vector2(entry.x, entry.z)) + Vector2(-7,-7),
				title, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color("#e5e6d5"))
	var center := screen(player_at)
	var forward := Vector2(-sin(heading), -cos(heading))
	var side := Vector2(-forward.y, forward.x)
	draw_colored_polygon(PackedVector2Array([center + forward * 9, center - forward * 5 + side * 5,
		center - forward * 5 - side * 5]), Color("#f2e3bb"))
	draw_circle(screen(marker), 4.0, Color("#eeb786"), false, 1.4, true)
	draw_string(get_theme_default_font(), Vector2(size.x - 33, 27), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color("#e5e6d5"))
	if expanded:
		draw_string(get_theme_default_font(), Vector2(12, size.y - 9),
			tr("© OpenStreetMap contributors · amber: playable landmark"), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color("#adbdb1"))


func screen(p: Vector2) -> Vector2:
	return view_origin + p * view_factor


func polygon(points: Array) -> PackedVector2Array:
	var result := PackedVector2Array()
	for raw in points:
		result.append(screen(Vector2(raw[0], raw[1])))
	return result
