class_name CampusSite
extends Node3D

const LAND := "res://assets/polyhaven/"
const ARCH := "res://assets/architecture/"
const FOOTWAYS := ["footway", "path", "cycleway"]
const SITE_LIMIT := Rect2(-156, -344, 632, 542)
const MAIN_LOD := [
	preload("res://assets/architecture/menara_razak_lod0.glb"),
	preload("res://assets/architecture/menara_razak_lod1.glb"),
	preload("res://assets/architecture/menara_razak_lod2.glb"),
]
const MAIN_COLLISION := preload("res://assets/architecture/menara_razak_collision.glb")
const MJIIT_LOD := [
	preload("res://assets/architecture/mjiit_lod0.glb"),
	preload("res://assets/architecture/mjiit_lod1.glb"),
	preload("res://assets/architecture/mjiit_lod2.glb"),
]
const MJIIT_COLLISION := preload("res://assets/architecture/mjiit_collision.glb")
const PLAZA := Vector2(-26, 23)
const SPAWN := Vector2(-49, 51)
const ROOM := Vector3(10, -110, 9)

var campus: Dictionary
var ground_values: Array
var grid_origin: Vector2
var grid_step: float
var materials := {}
const NEUTRAL_PAINT := preload("res://assets/materials/paint_neutral.jpg")
var exterior := Node3D.new()
var interior := Node3D.new()
var tower := Node3D.new()
var lod := 0
var mjiit_lod := 0
var mjiit := Node3D.new()
var southeast: Array[Dictionary] = []
var road: StandardMaterial3D
var night_panels: Array[StandardMaterial3D] = []
var street_lights: Array[OmniLight3D] = []


func _ready() -> void:
	campus = JSON.parse_string(FileAccess.get_file_as_string("res://data/map.json"))
	ground_values = campus.grid.heights
	grid_origin = Vector2(campus.grid.x, campus.grid.z)
	grid_step = campus.grid.step
	exterior.name = "Exterior"
	add_child(exterior)
	materials.grass = scanned("grass_ground", Color(0.43, 0.58, 0.46), Vector2.ONE, 0.7)
	materials.pavers = scanned("concrete_pavers", Color(0.86, 0.84, 0.78), Vector2.ONE, 0.45)
	materials.concrete = scanned("concrete_wall_008", Color(0.86, 0.88, 0.86), Vector2.ONE, 0.32)
	materials.column = scanned("concrete_floor_02", Color(0.83, 0.83, 0.77), Vector2.ONE, 0.3)
	materials.roof = scanned("box_profile_metal_sheet", Color(0.80, 0.83, 0.84), Vector2(1.0, 0.24), 0.32)
	materials.roof.albedo_texture = preload("res://assets/materials/roof_silver.jpg")
	materials.soil = scanned("red_laterite_soil_stones", Color(0.60, 0.58, 0.51), Vector2.ONE, 0.6)
	materials.tile = scanned("interior_tiles", Color(0.93, 0.89, 0.82), Vector2(0.36, 0.36), 0.38)
	materials.wood = scanned("old_wood_floor", Color(0.72, 0.60, 0.45), Vector2.ONE, 0.3)
	materials.wall = scanned("painted_concrete", Color(0.93, 0.90, 0.81), Vector2.ONE, 0.23)
	materials.wall.albedo_texture = NEUTRAL_PAINT
	materials.marking = solid(Color(0.87, 0.84, 0.69), 0.75)
	materials.turf = scanned("grass_ground", Color(0.63, 0.79, 0.51), Vector2.ONE, 0.6)
	road = scanned("aerial_asphalt_01", Color(0.82, 0.83, 0.83), Vector2.ONE, 0.72)
	build_terrain()
	build_roadways()
	build_tower()
	build_mjiit()
	add_southeast("residensi", "osm-way-524812098", "Residensi_UTMKL", Vector3(256, 24, 89))
	add_southeast("masjid", "osm-way-772103594", "Masjid_UTMKL", Vector3(108, 3, 165))
	build_plaza()
	build_reading_room()


func scanned(id: String, tint: Color, uv_scale: Vector2, strength: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	var path := LAND + id + "/"
	material.albedo_color = tint
	material.albedo_texture = load(path + "albedo.jpg")
	material.roughness_texture = load(path + "roughness.jpg")
	material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	material.normal_enabled = true
	material.normal_texture = load(path + "normal.png")
	material.normal_scale = strength
	material.uv1_scale = Vector3(uv_scale.x, uv_scale.y, 1)
	material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return material


func solid(color: Color, roughness: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	return material


func ground_height(point: Vector2) -> float:
	var size := Vector2i(ground_values[0].size(), ground_values.size())
	var at := (point - grid_origin) / grid_step
	var ix := clampi(floori(at.x), 0, size.x - 2)
	var iz := clampi(floori(at.y), 0, size.y - 2)
	var fx := clampf(at.x - ix, 0.0, 1.0)
	var fz := clampf(at.y - iz, 0.0, 1.0)
	# Same diagonal as the collision mesh.
	var a := float(ground_values[iz][ix])
	var b := float(ground_values[iz][ix + 1])
	var c := float(ground_values[iz + 1][ix])
	var d := float(ground_values[iz + 1][ix + 1])
	if fx + fz < 1.0:
		return a + (b - a) * fx + (c - a) * fz
	return d + (c - d) * (1.0 - fx) + (b - d) * (1.0 - fz)


func world_point(point: Vector2, above := 0.0) -> Vector3:
	return Vector3(point.x, ground_height(point) + above, point.y)


func point(raw: Array) -> Vector2:
	return Vector2(raw[0], raw[1])


func mesh_surface(material: Material) -> SurfaceTool:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	surface.set_material(material)
	return surface


func triangle(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, tile_size: float) -> void:
	for vertex in [a, b, c]:
		surface.set_uv(Vector2(vertex.x, vertex.z) / tile_size)
		surface.add_vertex(vertex)


func quad(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, tile_size: float) -> void:
	triangle(surface, a, b, c, tile_size)
	triangle(surface, b, d, c, tile_size)


func finish(surface: SurfaceTool, parent: Node3D, id: String, collision := false) -> MeshInstance3D:
	surface.generate_normals()
	surface.generate_tangents()
	surface.index()
	var node := MeshInstance3D.new()
	node.name = id
	node.mesh = surface.commit()
	parent.add_child(node)
	if collision:
		node.create_trimesh_collision()
	return node


func build_terrain() -> void:
	var rows := ground_values.size() - 1
	var columns: int = ground_values[0].size() - 1
	for z0 in range(0, rows, 16):
		for x0 in range(0, columns, 16):
			var surface := mesh_surface(materials.grass)
			for z in range(z0, mini(z0 + 16, rows)):
				for x in range(x0, mini(x0 + 16, columns)):
					var a := grid_origin + Vector2(x, z) * grid_step
					quad(surface, world_point(a), world_point(a + Vector2(grid_step, 0)),
						world_point(a + Vector2(0, grid_step)), world_point(a + Vector2.ONE * grid_step), 4.2)
			finish(surface, exterior, "Terrain_%d_%d" % [x0, z0], true)


func samples(route: Array) -> PackedVector2Array:
	var expanded := PackedVector2Array([point(route[0])])
	for i in range(1, route.size()):
		var a := point(route[i - 1])
		var b := point(route[i])
		var count := ceili(a.distance_to(b) / 1.7)
		for j in range(1, count + 1):
			expanded.append(a.lerp(b, float(j) / count))
	return expanded


func ribbon(surface: SurfaceTool, route: PackedVector2Array, width: float, above: float, repeat_m: float) -> void:
	var previous_left := Vector3.ZERO
	var previous_right := Vector3.ZERO
	var terrain_edge := Rect2(grid_origin + Vector2(4,4),
		Vector2(ground_values[0].size() - 1, ground_values.size() - 1) * grid_step - Vector2(8,8))
	var contiguous := false
	for i in route.size():
		if not terrain_edge.has_point(route[i]):
			contiguous = false
			continue
		var tangent := (route[mini(i + 1, route.size() - 1)] - route[maxi(i - 1, 0)]).normalized()
		var right := Vector2(-tangent.y, tangent.x) * width * 0.5
		var left_point := world_point(route[i] - right, above)
		var right_point := world_point(route[i] + right, above)
		if contiguous:
			quad(surface, previous_left, left_point, previous_right, right_point, repeat_m)
		contiguous = true
		previous_left = left_point
		previous_right = right_point


func build_roadways() -> void:
	var asphalt := mesh_surface(road)
	var paths := mesh_surface(materials.pavers)
	var road_marks := mesh_surface(materials.marking)
	for lot in campus.parking:
		var perimeter := PackedVector2Array()
		for coord in lot.points:
			perimeter.append(point(coord))
		var faces := Geometry2D.triangulate_polygon(perimeter)
		for i in range(0, faces.size(), 3):
			slope_patch(asphalt, perimeter[faces[i]], perimeter[faces[i+1]], perimeter[faces[i+2]], .031)
	for route in campus.roads:
		var route_points := samples(route.points)
		if route_points.size() < 2:
			continue
		var pedestrian: bool = route.type in FOOTWAYS
		var elevation := 0.095 if pedestrian else 0.044 + float(int(route.id) % 11) * 0.002
		ribbon(paths if pedestrian else asphalt, route_points, route.width, elevation, 3.0 if pedestrian else 8.0)
		if route.type == "secondary":
			for j in range(0, route_points.size() - 3, 6):
				ribbon(road_marks, route_points.slice(j, j + 3), 0.13, 0.078, 1.0)
	finish(asphalt, exterior, "OSM_Asphalt")
	finish(paths, exterior, "OSM_Walkways")
	finish(road_marks, exterior, "RoadMarkings")


func slope_patch(surface: SurfaceTool, a: Vector2, b: Vector2, c: Vector2, elevation: float) -> void:
	if maxf(a.distance_to(b), maxf(b.distance_to(c), c.distance_to(a))) <= 5.5:
		triangle(surface, world_point(a,elevation), world_point(b,elevation), world_point(c,elevation), 5.8)
		return
	var ab := (a+b) * .5
	var bc := (b+c) * .5
	var ca := (c+a) * .5
	slope_patch(surface, a, ab, ca, elevation)
	slope_patch(surface, ab, b, bc, elevation)
	slope_patch(surface, ca, bc, c, elevation)
	slope_patch(surface, ab, bc, ca, elevation)


func build_tower() -> void:
	tower.name = "Menara_Razak_OSM_552610255"
	tower.position.y = float(campus.tower_base_y)
	exterior.add_child(tower)
	for index in MAIN_LOD.size():
		var instance := MAIN_LOD[index].instantiate() as Node3D
		instance.name = "LOD%d" % index
		tower.add_child(instance)
		instance.visible = index == lod
		for mesh in instance.find_children("*", "MeshInstance3D", true, false):
			match String(mesh.name):
				"Concrete":
					mesh.material_override = materials.concrete
				"RoofCladding":
					mesh.material_override = materials.roof
				"GlassNight":
					var panel := mesh.mesh.surface_get_material(0).duplicate() as StandardMaterial3D
					panel.emission_enabled = true
					panel.emission = Color(1.0, 0.76, 0.46)
					panel.emission_energy_multiplier = 0.0
					mesh.material_override = panel
					night_panels.append(panel)
	var shell := MAIN_COLLISION.instantiate() as Node3D
	tower.add_child(shell)
	for mesh in shell.find_children("*", "MeshInstance3D", true, false):
		mesh.create_trimesh_collision()
		mesh.hide()
	var sign := label_3d(tower, "MENARA RAZAK", Vector3(-1.19, 3.69, 15.15), 0.013, Color(0.96, 0.90, 0.80))
	sign.rotation.y = -0.656


func build_mjiit() -> void:
	var entry: Dictionary
	for building in campus.buildings:
		if building.id == "osm-way-733313948":
			entry = building
			break
	mjiit.name = "MJIIT_OSM_733313948"
	exterior.add_child(mjiit)
	mjiit.position.y = float(entry.altitude_m) - float(campus.vertical_origin_m)
	var yellow := scanned("painted_concrete", Color("#bb9859"), Vector2.ONE, .27)
	var blue := scanned("painted_concrete", Color("#83a4b6"), Vector2.ONE, .21)
	yellow.albedo_texture = NEUTRAL_PAINT
	blue.albedo_texture = NEUTRAL_PAINT
	for index in MJIIT_LOD.size():
		var instance := MJIIT_LOD[index].instantiate() as Node3D
		instance.name = "LOD%d" % index
		mjiit.add_child(instance)
		instance.visible = index == 0
		for mesh in instance.find_children("*", "MeshInstance3D", true, false):
			match String(mesh.name):
				"WarmBase":
					mesh.material_override = yellow
				"PaintCream":
					mesh.material_override = materials.wall
				"PaintBlue":
					mesh.material_override = blue
				"Roof":
					mesh.material_override = materials.roof
	var shell := MJIIT_COLLISION.instantiate() as Node3D
	mjiit.add_child(shell)
	for mesh in shell.find_children("*", "MeshInstance3D", true, false):
		mesh.create_trimesh_collision()
		mesh.hide()
	var sign := label_3d(mjiit, "MJIIT", Vector3(108,15.3,46), 0.048, Color("#7a2435"))
	sign.rotation.y = -PI / 2


func add_southeast(slug: String, id: String, label_text: String, focus: Vector3) -> void:
	var datum: Dictionary
	for building in campus.buildings:
		if building.id == id:
			datum = building
			break
	var model := Node3D.new()
	model.name = label_text
	model.position.y = float(datum.altitude_m) - float(campus.vertical_origin_m)
	exterior.add_child(model)
	var warm := scanned("painted_concrete", Color("#ae9d77"), Vector2.ONE, .26)
	warm.albedo_texture = NEUTRAL_PAINT
	var blue := scanned("box_profile_metal_sheet", Color("#5d829e"), Vector2(1,.42), .30)
	blue.albedo_texture = materials.roof.albedo_texture
	var screens := scanned("box_profile_metal_sheet", Color("#939599"), Vector2(1,.65), .22)
	screens.albedo_texture = materials.roof.albedo_texture
	for level in 3:
		var scene := load(ARCH + slug + "_lod%d.glb" % level) as PackedScene
		var lod_model := scene.instantiate() as Node3D
		lod_model.name = "LOD%d" % level
		model.add_child(lod_model)
		lod_model.visible = level == 0
		for mesh in lod_model.find_children("*", "MeshInstance3D", true, false):
			match String(mesh.name):
				"Stone":
					mesh.material_override = materials.concrete
				"PaintWhite":
					mesh.material_override = materials.wall
				"PaintWarm":
					mesh.material_override = warm
				"RoofBlue":
					mesh.material_override = blue
				"Screen":
					mesh.material_override = screens
	var collision := load(ARCH + slug + "_collision.glb") as PackedScene
	var shell := collision.instantiate() as Node3D
	model.add_child(shell)
	for mesh in shell.find_children("*", "MeshInstance3D", true, false):
		mesh.create_trimesh_collision()
		mesh.hide()
	southeast.append({"node": model, "center": focus, "lod": 0})


func change_lod(building: Node3D, current: int, distance: float) -> int:
	var desired := 0 if distance < 105.0 else (1 if distance < 228.0 else 2)
	if desired != current:
		building.get_node("LOD%d" % current).hide()
		building.get_node("LOD%d" % desired).show()
	return desired


func set_lod(eye: Vector3) -> void:
	lod = change_lod(tower, lod, eye.distance_to(Vector3(7, tower.position.y + 23.0, 7)))
	mjiit_lod = change_lod(mjiit, mjiit_lod, eye.distance_to(Vector3(136.5, mjiit.position.y + 16, 53)))
	for block_info in southeast:
		block_info.lod = change_lod(block_info.node, block_info.lod, eye.distance_to(block_info.center))


func prop(id: String, parent: Node3D, location: Vector3, yaw: float, prop_scale := 1.0) -> Node3D:
	var path := "res://assets/landscape/island_tree_realtime.glb" if id == "island_tree_02" else LAND + id + "/" + id + ".gltf"
	var scene := load(path) as PackedScene
	var item := scene.instantiate() as Node3D
	parent.add_child(item)
	item.position = location
	item.rotation.y = yaw
	item.scale = Vector3.ONE * prop_scale
	return item


func place_props(id: String, placements: Array) -> void:
	# Keep source transforms, instance repeated static props per material/mesh.
	var source := prop(id, exterior, Vector3.ZERO, 0.0)
	for original in source.find_children("*", "MeshInstance3D", true, false):
		var instances := MultiMesh.new()
		instances.transform_format = MultiMesh.TRANSFORM_3D
		instances.mesh = original.mesh
		instances.instance_count = placements.size()
		for i in placements.size():
			var spec: Vector4 = placements[i]
			var basis := Basis(Vector3.UP, spec.z).scaled(Vector3.ONE * spec.w)
			var location := world_point(Vector2(spec.x, spec.y))
			instances.set_instance_transform(i, Transform3D(basis, location) * original.global_transform)
		var batch := MultiMeshInstance3D.new()
		batch.multimesh = instances
		batch.visibility_range_end = 550.0
		batch.visibility_range_end_margin = 22.0
		exterior.add_child(batch)
	source.queue_free()


func flat_patch(parent: Node3D, id: String, bounds: Rect2, material: Material, above: float) -> void:
	var surface := mesh_surface(material)
	for j in range(ceili(bounds.size.y / 2)):
		for i in range(ceili(bounds.size.x / 2)):
			var a := bounds.position + Vector2(i * 2, j * 2)
			var dx := minf(2.0, bounds.end.x - a.x)
			var dz := minf(2.0, bounds.end.y - a.y)
			quad(surface, world_point(a, above), world_point(a + Vector2(dx, 0), above),
				world_point(a + Vector2(0, dz), above), world_point(a + Vector2(dx, dz), above), 2.2)
	finish(surface, parent, id)


func build_plaza() -> void:
	# Placement is interpretive and is limited to the Menara Razak showcase.
	flat_patch(exterior, "Forecourt", Rect2(-32, 14, 17, 14), materials.pavers, 0.12)
	flat_patch(exterior, "PlantBed", Rect2(-25.8, 22, 4.8, 6.0), materials.soil, 0.15)
	place_props("island_tree_02", [
		Vector4(-29, 22, 1.6, 2.12), Vector4(-19, 36, 1.1, 2.38),
		Vector4(-42, 48, 2.1, 2.09), Vector4(-37, 71, 0.2, 2.45),
		Vector4(-72, 49, 2.3, 2.70), Vector4(-65, 22, 1.3, 2.12),
		Vector4(-79, -1, 2.9, 2.35), Vector4(-47, -54, 1.5, 2.09),
		Vector4(12, -42, 2.6, 2.20), Vector4(40, -39, 1.9, 2.14),
		Vector4(35, 57, 0.3, 2.20), Vector4(52, 70, 2.1, 2.15),
		Vector4(79, 82, 0.5, 2.04), Vector4(86, 52, 2.8, 1.68),
		Vector4(88, 10, 3.0, 1.95), Vector4(102, -8, .15, 2.32),
		Vector4(-77, 57, .47, 3.0), Vector4(-52, 66, .84, 2.32),
		Vector4(88, 160, 1.2, 2.77), Vector4(111, 198, .6, 2.5),
		Vector4(180, 118, .4, 2.23), Vector4(223, 147, .7, 2.14),
	])
	place_props("street_lamp_01", [
		Vector4(-30, 15, 0.7, 0.8), Vector4(-13, 36, -1.1, 0.8),
		Vector4(-54, 38, 0.7, 0.8), Vector4(-53, 76, 1.8, 0.8),
	])
	for pos in [Vector2(-30, 15), Vector2(-13, 36), Vector2(-54, 38), Vector2(-53, 76)]:
		var light := OmniLight3D.new()
		light.light_color = Color(1.0, 0.79, 0.54)
		light.light_energy = 0.0
		light.omni_range = 14.0
		exterior.add_child(light)
		light.position = world_point(pos, 4.0)
		street_lights.append(light)
	place_props("painted_wooden_bench", [Vector4(-28, 23, 0.2, 1.0), Vector4(-22, 25, -0.4, 1.0)])
	place_props("metal_trash_can", [Vector4(-30, 25, 0.2, 0.62)])
	place_props("planter_box_01", [Vector4(-26, 18, 0.3, 1.0), Vector4(-19, 21, 0.3, 1.0)])


func block(parent: Node3D, title: String, center: Vector3, size: Vector3, material: Material, collision := true) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var instance := MeshInstance3D.new()
	instance.name = title
	instance.mesh = mesh
	instance.material_override = material
	parent.add_child(instance)
	instance.position = center
	if collision:
		instance.create_trimesh_collision()
	return instance


func label_3d(parent: Node3D, words: String, at: Vector3, pixel_scale: float, tint: Color) -> Label3D:
	var sign := Label3D.new()
	sign.text = words
	sign.pixel_size = pixel_scale
	sign.modulate = tint
	sign.font_size = 55
	sign.outline_size = 0
	parent.add_child(sign)
	sign.position = at
	return sign


func build_reading_room() -> void:
	interior.name = "Fictional_Reading_Room"
	interior.position = ROOM
	add_child(interior)
	block(interior, "Tile_Floor", Vector3(0,-0.1,0), Vector3(17,0.2,12), materials.tile)
	block(interior, "Ceiling", Vector3(0,3.9,0), Vector3(17,0.25,12), materials.wall)
	for x in [-8.5, 8.5]:
		block(interior, "Side_Wall", Vector3(x,1.9,0), Vector3(0.24,4,12), materials.wall)
	for z in [-6, 6]:
		block(interior, "End_Wall", Vector3(0,1.9,z), Vector3(17,4,0.24), materials.wall)
	var book_colors: Array[Material] = [
		solid(Color("#586777"),0.83), solid(Color("#b4946e"),0.75), solid(Color("#682e39"),0.72),
		solid(Color("#427064"),0.78), solid(Color("#a09776"),0.7),
	]
	for rack in range(3):
		var x := -5.9 + rack * 2.9
		for level in range(4):
			var y := 0.36 + level * 0.51
			block(interior, "Shelf", Vector3(x,y,-5.05), Vector3(2.56,0.055,0.44), materials.wood, false)
			for book in range(14):
				var book_height := 0.24 + float((book * 7 + rack + level) % 11) * 0.013
				var book_depth := 0.13 + float(book % 6)*0.018
				block(interior, "Book", Vector3(x - 1.12 + 0.16 * book,y+0.03+book_height/2,-4.97),
					Vector3(0.142,book_height,book_depth), book_colors[(level+book+rack)%book_colors.size()], false)
		block(interior, "Shelf_Side", Vector3(x - 1.24,1.08,-5.05), Vector3(0.06,2.15,0.44), materials.wood, false)
		block(interior, "Shelf_Side", Vector3(x + 1.24,1.08,-5.05), Vector3(0.06,2.15,0.44), materials.wood, false)
		block(interior, "Shelf_Collision", Vector3(x,1.1,-5.06), Vector3(2.57,2.2,0.45), materials.wall).hide()
	for z in [-1.7, 1.6]:
		for x in [-3.8, 2.2]:
			block(interior, "Tabletop", Vector3(x,0.78,z), Vector3(2.5,0.065,1.02), materials.wood)
			for leg in [-1, 1]:
				block(interior, "Table_Legs", Vector3(x+leg*1.06,0.38,z), Vector3(0.09,0.75,0.70), materials.wood, false)
			prop("painted_wooden_bench", interior, Vector3(x,0,z+0.96), PI)
			prop("painted_wooden_bench", interior, Vector3(x,0,z-0.96), 0)
	var diffuser := solid(Color("#f6dfb3"), 0.48)
	diffuser.emission_enabled = true
	diffuser.emission = Color("#ffd8a8")
	diffuser.emission_energy_multiplier = 1.3
	for x in [-5.0, 0.0, 5.0]:
		var lamp := OmniLight3D.new()
		lamp.light_color = Color("#ffe7c4")
		lamp.light_energy = 2.0
		lamp.omni_range = 10.0
		interior.add_child(lamp)
		lamp.position = Vector3(x,3.38,0)
		block(interior,"Light_strip",Vector3(x,3.73,0),Vector3(0.21,0.06,4.5),diffuser,false)
	label_3d(interior, "BILIK BACAAN", Vector3(3.3,2.55,-5.84), .015, Color("#605143"))
	label_3d(interior, "FICTIONAL READING ROOM", Vector3(3.3,2.07,-5.83), .0069, Color("#856849"))
	interior.hide()
