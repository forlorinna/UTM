class_name CampusSite
extends Node3D

const LAND := "res://assets/polyhaven/"
const ARCH := "res://assets/architecture/"
const FOOTWAYS := ["footway", "path", "cycleway"]
const SITE_LIMIT := Rect2(-156, -344, 632, 542)
const MAIN_LOD := [
	preload("res://assets/runtime/buildings/menara_razak/menara_razak_lod0.glb"),
	preload("res://assets/runtime/buildings/menara_razak/menara_razak_lod1.glb"),
	preload("res://assets/runtime/buildings/menara_razak/menara_razak_lod2.glb"),
]
const MAIN_COLLISION := preload("res://assets/runtime/buildings/menara_razak/menara_razak_collision.glb")
const MJIIT_LOD := [
	preload("res://assets/runtime/buildings/mjiit/mjiit_lod0.glb"),
	preload("res://assets/runtime/buildings/mjiit/mjiit_lod1.glb"),
	preload("res://assets/runtime/buildings/mjiit/mjiit_lod2.glb"),
]
const MJIIT_COLLISION := preload("res://assets/runtime/buildings/mjiit/mjiit_collision.glb")
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
var gate := Node3D.new()
var gate_lod := 0
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
	materials.grass = RealityMaterials.terrain_layer()
	materials.pavers = RealityMaterials.surface("interlocking_concrete_pavers", Color(0.82, 0.80, 0.75), Vector2.ONE, 0.62)
	materials.concrete = scanned("concrete_wall_008", Color(0.86, 0.88, 0.86), Vector2.ONE, 0.32)
	materials.column = scanned("concrete_floor_02", Color(0.83, 0.83, 0.77), Vector2.ONE, 0.3)
	materials.roof = scanned("box_profile_metal_sheet", Color(0.80, 0.83, 0.84), Vector2(1.0, 0.24), 0.32)
	materials.roof.albedo_texture = preload("res://assets/materials/roof_silver.jpg")
	materials.soil = RealityMaterials.surface("forest_ground_05", Color(0.79, 0.75, 0.62), Vector2.ONE, 0.63)
	materials.tile = scanned("interior_tiles", Color(0.93, 0.89, 0.82), Vector2(0.36, 0.36), 0.38)
	materials.wood = scanned("old_wood_floor", Color(0.72, 0.60, 0.45), Vector2.ONE, 0.3)
	materials.wall = scanned("painted_concrete", Color(0.93, 0.90, 0.81), Vector2.ONE, 0.23)
	materials.wall.albedo_texture = NEUTRAL_PAINT
	materials.marking = solid(Color(0.87, 0.84, 0.69), 0.75)
	materials.turf = scanned("grass_ground", Color(0.63, 0.79, 0.51), Vector2.ONE, 0.6)
	road = RealityMaterials.surface("asphalt_03", Color(0.89, 0.90, 0.87), Vector2.ONE, 0.58)
	materials.curbs = RealityMaterials.surface("gravel_embedded_concrete", Color("#b8b4a4"), Vector2.ONE, 0.54)
	materials.plaza = RealityMaterials.surface("grey_stone_path", Color("#c8c9bd"), Vector2.ONE, 0.60)
	materials.road_patch = RealityMaterials.surface("worn_asphalt", Color("#c2beb0"), Vector2.ONE, 0.56)
	materials.drain = RealityMaterials.surface("metal_grate_rusty", Color("#7b7970"), Vector2.ONE, 0.54, 0.45)
	build_terrain()
	build_roadways()
	build_tower()
	build_mjiit()
	build_main_gate()
	build_residensi()
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
	var raised_edges := mesh_surface(materials.curbs)
	var surface_repairs := mesh_surface(materials.road_patch)
	var drains := mesh_surface(materials.drain)
	var road_edge_ids := ["611389407", "854288227"]
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
		ribbon(paths if pedestrian else asphalt, route_points, route.width, elevation, 3.0 if pedestrian else 4.0)
		if str(route.id) in road_edge_ids and route_points.size() > 6:
			road_hardscape(raised_edges, surface_repairs, drains, route_points, route.width, elevation)
		if route.type == "secondary":
			for j in range(0, route_points.size() - 3, 6):
				ribbon(road_marks, route_points.slice(j, j + 3), 0.13, 0.078, 1.0)
	finish(asphalt, exterior, "OSM_Asphalt")
	finish(paths, exterior, "OSM_Walkways")
	finish(road_marks, exterior, "RoadMarkings")
	finish(raised_edges, exterior, "RaisedCurbs")
	finish(surface_repairs, exterior, "AsphaltRepairCourses")
	finish(drains, exterior, "SlotDrains")


func road_hardscape(edges: SurfaceTool, patches: SurfaceTool, drains: SurfaceTool,
		route: PackedVector2Array, width: float, h: float) -> void:
	for i in range(2, route.size() - 3):
		var a := route[i]
		var b := route[i+1]
		var before := (route[i+1] - route[i-1]).normalized()
		var after := (route[i+2] - route[i]).normalized()
		for side: float in [-1.0, 1.0]:
			var offset_a := Vector2(-before.y, before.x) * side
			var offset_b := Vector2(-after.y, after.x) * side
			var outer_a := a + offset_a * (width*0.5+.14)
			var outer_b := b + offset_b * (width*0.5+.14)
			var inner_a := a + offset_a * width*0.5
			var inner_b := b + offset_b * width*0.5
			var x1 := world_point(inner_a, h+.12)
			var x2 := world_point(inner_b, h+.12)
			var y1 := world_point(outer_a, h+.12)
			var y2 := world_point(outer_b, h+.12)
			if side < 0.0:
				quad(edges, y1, y2, x1, x2, 1.8)
			else:
				quad(edges, x1, x2, y1, y2, 1.8)
			if side < 0.0:
				quad(edges, x1, x2, world_point(inner_a,h), world_point(inner_b,h), 1.8)
			else:
				quad(edges, x2, x1, world_point(inner_b,h), world_point(inner_a,h), 1.8)
			if i % 12 == 5:
				var drain_a := a + offset_a * (width*.5-.36)
				var drain_b := b + offset_b * (width*.5-.36)
				var uv_a := world_point(drain_a,h+.018)
				var uv_b := world_point(drain_b,h+.018)
				if side < 0.0:
					quad(drains, world_point(inner_a,h+.018), world_point(inner_b,h+.018), uv_a, uv_b, 1.2)
				else:
					quad(drains, uv_a, uv_b, world_point(inner_a,h+.018), world_point(inner_b,h+.018), 1.2)
		if i % 8 == 3:
			ribbon(patches, route.slice(i,i+2), 0.85, h+.016, 2.8)


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
	var limestone := RealityMaterials.surface("rectangular_facade_tiles_02", Color("#c3bdb1"), Vector2.ONE, .16)
	var precast := RealityMaterials.surface("concrete_panels", Color("#bfc3cc"), Vector2.ONE, .19)
	add_rebuilt(tower, "osm-way-552610255", MAIN_LOD, MAIN_COLLISION, {
		"Precast": precast,
		"Sandstone": limestone,
		"Granite": RealityMaterials.surface("anti_skid_tiles", Color("#8f887b"), Vector2.ONE, .53),
		"Paving": materials.plaza,
		"RoofSeam": RealityMaterials.surface("metal_plate_02", Color("#abaeb2"), Vector2(0.67,1.0), .28, .54),
		"RoofDeck": RealityMaterials.surface("brushed_concrete_03", Color("#8b8c8c"), Vector2.ONE, .41),
	})
	var sign := label_3d(tower, "MENARA RAZAK", Vector3(-1.735, 3.631, 14.829), 0.017, Color("#e2dbc9"))
	sign.rotation.y = -0.656
	add_entry_light(Vector3(-3.8, tower.position.y + 3.52, 16.2))
	add_entry_light(Vector3(2.1, tower.position.y + 3.52, 20.65))


func build_mjiit() -> void:
	for entry in campus.buildings:
		if entry.id == "osm-way-733313948":
			mjiit.position.y = float(entry.altitude_m) - float(campus.vertical_origin_m)
			break
	mjiit.name = "MJIIT_OSM_733313948"
	add_rebuilt(mjiit, "osm-way-733313948", MJIIT_LOD, MJIIT_COLLISION, {
		"Ivory": RealityMaterials.surface("brushed_concrete_03", Color("#ccc8b5"), Vector2.ONE, .31),
		"BluePlaster": RealityMaterials.surface("painted_plaster_wall", Color("#7795a3"), Vector2.ONE, .31),
		"Ochre": RealityMaterials.surface("painted_plaster_wall", Color("#cbab70"), Vector2.ONE, .38),
		"Paving": materials.plaza,
	})
	var sign := label_3d(mjiit, "MJIIT", Vector3(107.50,13.94,45), 0.046, Color("#7a2435"))
	sign.rotation.y = -PI / 2.0
	var plate := label_3d(mjiit, "MALAYSIA–JAPAN INTERNATIONAL INSTITUTE OF TECHNOLOGY", Vector3(107.98,10.69,45), 0.010, Color("#eee7d4"))
	plate.rotation.y = -PI / 2.0
	add_entry_light(Vector3(108.1, mjiit.position.y + 3.35, 40.5))
	add_entry_light(Vector3(108.1, mjiit.position.y + 3.35, 51.4))


func add_rebuilt(building: Node3D, id: String, levels: Array, collider: PackedScene, overrides: Dictionary) -> void:
	exterior.add_child(building)
	building.set_meta("building_id", id)
	building.set_meta("reality_rebuild", true)
	for level in levels.size():
		var prefab := levels[level] as PackedScene
		var model := prefab.instantiate() as Node3D
		model.name = "LOD%d" % level
		model.set_meta("asset_path", prefab.resource_path)
		building.add_child(model)
		model.visible = level == 0
		for mesh in model.find_children("*", "MeshInstance3D", true, false):
			var finish_name := String(mesh.name)
			if overrides.has(finish_name):
				mesh.material_override = overrides[finish_name]
			elif finish_name == "Lit":
				var light_surface := mesh.mesh.surface_get_material(0).duplicate() as StandardMaterial3D
				light_surface.emission_enabled = true
				light_surface.emission = Color("#ffd3a0")
				light_surface.emission_energy_multiplier = 0.0
				mesh.material_override = light_surface
				night_panels.append(light_surface)
	var shell := collider.instantiate() as Node3D
	shell.name = "Collision"
	building.add_child(shell)
	for mesh in shell.find_children("*", "MeshInstance3D", true, false):
		mesh.create_trimesh_collision()
		mesh.hide()


func build_main_gate() -> void:
	const PREFIX := "res://assets/runtime/buildings/main_gate/main_gate_"
	gate.name = "UTMKL_Main_Entrance"
	gate.position = world_point(Vector2(-62.4, -5.65), .06)
	add_rebuilt(gate, "utmkl-main-entrance", [
		load(PREFIX + "lod0.glb"), load(PREFIX + "lod1.glb"), load(PREFIX + "lod2.glb")
	], load(PREFIX + "collision.glb"), {
		"Ochre": RealityMaterials.surface("rectangular_facade_tiles_02", Color("#a79569"), Vector2.ONE, .38),
		"Paving": RealityMaterials.surface("anti_slip_concrete", Color("#9c9585"), Vector2.ONE, .49),
	})
	var label := label_3d(gate, "UTM KUALA LUMPUR", Vector3(-1.08, 5.14, -0.74), .012, Color("#3a2b25"))
	label.rotation.y = -2.18
	add_entry_light(gate.position + Vector3(-.4, 3.27, -.63))


func build_residensi() -> void:
	const PREFIX := "res://assets/runtime/buildings/residensi_utmkl/residensi_utmkl_"
	const ID := "osm-way-524812098"
	var model := Node3D.new()
	model.name = "Residensi_UTMKL"
	for entry in campus.buildings:
		if entry.id == ID:
			model.position.y = float(entry.altitude_m) - float(campus.vertical_origin_m)
			break
	add_rebuilt(model, ID, [
		load(PREFIX + "lod0.glb"), load(PREFIX + "lod1.glb"), load(PREFIX + "lod2.glb")
	], load(PREFIX + "collision.glb"), {
		"Ivory": RealityMaterials.surface("painted_plaster_wall", Color("#bcb5a0"), Vector2.ONE, .30),
		"Plinth": RealityMaterials.surface("concrete_panels", Color("#9f9783"), Vector2.ONE, .39),
		"RoofDeck": RealityMaterials.surface("brushed_concrete_03", Color("#8b8c8c"), Vector2.ONE, .41),
		"Paving": materials.plaza,
	})
	southeast.append({"node": model, "center": Vector3(256, 24, 89), "lod": 0})


func add_entry_light(at: Vector3) -> void:
	var lamp := OmniLight3D.new()
	lamp.light_color = Color("#ffe2b9")
	lamp.light_energy = 0.0
	lamp.omni_range = 8.3
	lamp.omni_attenuation = 2.0
	exterior.add_child(lamp)
	lamp.position = at
	street_lights.append(lamp)


func add_southeast(slug: String, id: String, label_text: String, focus: Vector3) -> void:
	var datum: Dictionary
	for building in campus.buildings:
		if building.id == id:
			datum = building
			break
	var model := Node3D.new()
	model.name = label_text
	model.set_meta("building_id", id)
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
	gate_lod = change_lod(gate, gate_lod, eye.distance_to(gate.position + Vector3.UP * 3.0))
	lod = change_lod(tower, lod, eye.distance_to(Vector3(7, tower.position.y + 23.0, 7)))
	mjiit_lod = change_lod(mjiit, mjiit_lod, eye.distance_to(Vector3(136.5, mjiit.position.y + 16, 53)))
	for block_info in southeast:
		block_info.lod = change_lod(block_info.node, block_info.lod, eye.distance_to(block_info.center))


func prop(id: String, parent: Node3D, location: Vector3, yaw: float, prop_scale := 1.0) -> Node3D:
	var path := "res://assets/landscape/island_tree_realtime.glb" if id == "island_tree_02" else LAND + id + "/" + id + ".gltf"
	for kind in ["vegetation", "props"]:
		var rebuilt_path: String = "res://assets/runtime/" + kind + "/" + id + ".glb"
		if ResourceLoader.exists(rebuilt_path):
			path = rebuilt_path
			break
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
		batch.set_meta("visual_asset", id)
		batch.set_meta("scene_path", source.scene_file_path)
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
	flat_patch(exterior, "Forecourt", Rect2(-32, 14, 17, 14), materials.plaza, 0.12)
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
	place_props("royal_palm", [
		Vector4(-66.0,-20.4,0.9,.64), Vector4(-71.5,-16.8,1.7,.58),
		Vector4(-76.8,-13.5,2.3,.56), Vector4(-83.3,-9.5,2.1,.67),
		Vector4(-29.0,18.2,0.6,.46), Vector4(-38.1,25.5,-.8,.54),
	])
	place_props("travelers_palm", [Vector4(-20.8, 25, 1.9,.52), Vector4(-31.7,16.1,-.4,.51),
		Vector4(89,44,1.55,.57), Vector4(82,48,2.0,.52)])
	place_props("coconut_palm", [Vector4(-73.1,28.2,1.3,.68), Vector4(-54,38,2.0,.65),
		Vector4(-18.3,42.8,.05,.63), Vector4(80.5,63.4,1.4,.59)])
	place_props("areca_palm", [Vector4(-27.1,17.2,-.3,.88), Vector4(-18.9,19,1.2,1.1),
		Vector4(107.4,35.5,1.4,.88), Vector4(105.1,54.45,.05,1.0)])
	place_props("fern_02", [Vector4(-23.1,22.6,1.8,.8), Vector4(-25.2,23.2,.24,.75),
		Vector4(-23.8,27.8,1.2,.68), Vector4(-22.0,27.2,2.6,.65), Vector4(-30.8,16.8,.3,.84),
		Vector4(-32.5,19.2,1.3,.77), Vector4(-68,-3.2,-.76,1.05)])
	place_props("periwinkle_plant", [Vector4(-23.8,25.7,.9,.76), Vector4(-22.6,26.0,1.8,.74),
		Vector4(-22.3,23.0,2.7,.81), Vector4(-24.5,26.0,1.6,.67)])
	place_props("grass_bermuda_01", [Vector4(-28,25.8,.1,1.2), Vector4(-29.2,25.1,.7,1.09),
		Vector4(-68,-3.8,.2,1.11), Vector4(-67.6,-2.7,2.0,1.18)])
	place_props("planter_box_02", [Vector4(-19.4,23.8,.21,.88), Vector4(-22.6,23.8,.21,.88)])
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
