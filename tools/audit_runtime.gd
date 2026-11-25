extends SceneTree

var binding_csv: FileAccess
var runtime_csv: FileAccess
var building_csv: FileAccess
var missing := 0
var warnings := 0


func _initialize() -> void:
	probe.call_deferred()


func probe() -> void:
	var args := OS.get_cmdline_user_args()
	var output := args[args.find("--audit") + 1] if args.has("--audit") else "/tmp/utmkl-runtime-audit"
	DirAccess.make_dir_recursive_absolute(output)
	binding_csv = FileAccess.open(output + "/material_bindings.csv", FileAccess.WRITE)
	runtime_csv = FileAccess.open(output + "/runtime_asset_audit.csv", FileAccess.WRITE)
	building_csv = FileAccess.open(output + "/building_audit.csv", FileAccess.WRITE)
	if binding_csv == null or runtime_csv == null or building_csv == null:
		push_error("Could not create runtime audit reports")
		quit(2)
		return
	binding_csv.store_csv_line(["building_id","lod","mesh","surface","material","channel","asset_id","image_path","width","height"])
	runtime_csv.store_csv_line(["building_id","lod","active","mesh","surface","material_override","material","asset_path","status"])
	building_csv.store_csv_line(["building_id","name","lod","active","asset_path","meshes","surfaces","collision_shapes","status"])

	var game := (load("res://scenes/campus.tscn") as PackedScene).instantiate()
	root.add_child(game)
	game.set_process(false)
	game.set_physics_process(false)
	await process_frame
	var site := game.site as CampusSite
	site.set_lod(game.explorer.lens.global_position)
	var buildings: Array[Node] = [site.tower, site.mjiit, site.gate]
	for record in site.southeast:
		buildings.append(record.node)
	for building in buildings:
		var building_id := str(building.get_meta("building_id", building.name))
		var collision := building.find_children("*", "CollisionShape3D", true, false).size()
		for level in 3:
			var node := building.get_node_or_null("LOD%d" % level) as Node3D
			if node == null:
				missing += 1
				building_csv.store_csv_line([building_id,building.name,str(level),"false","","0","0",str(collision),"missing_lod"])
				continue
			var path := str(node.get_meta("asset_path", node.scene_file_path))
			var meshes := node.find_children("*", "MeshInstance3D", true, false)
			var surfaces := 0
			var count_before := missing
			for mesh in meshes:
				surfaces += inspect_mesh(building_id, str(level), node.visible, mesh.name, mesh.mesh, mesh.material_override, path, mesh)
			var state := "loaded_rebuild" if building.get_meta("reality_rebuild",false) else "loaded_legacy_pending_rebuild"
			if missing != count_before or collision == 0 or surfaces == 0:
				state = "needs_review"
			building_csv.store_csv_line([building_id,building.name,str(level),str(node.visible),path,str(meshes.size()),
				str(surfaces),str(collision),state])

	for node in site.exterior.find_children("*", "MeshInstance3D", true, false):
		if node.get_parent() != site.exterior:
			continue
		inspect_mesh("campus_terrain_and_streets","base",node.visible,node.name,node.mesh,node.material_override,"generated mesh",node)
	for node in site.exterior.find_children("*", "MultiMeshInstance3D", true, false):
		if node.multimesh == null:
			continue
		var resource := str(node.get_meta("visual_asset", "street_prop"))
		inspect_mesh(resource,"instanced",node.visible,node.name,node.multimesh.mesh,node.material_override,
			str(node.get_meta("scene_path","")),null)

	var sky := game.atmosphere as CampusAtmosphere
	for i in sky.panoramas.size():
		texture_binding("campus_environment",str(i),"Panorama",0,"Photographic HDRI","Panorama",sky.panoramas[i].panorama)

	var details := FileAccess.open(output + "/render_capabilities.json", FileAccess.WRITE)
	details.store_string(JSON.stringify({
		"godot": Engine.get_version_info().string,
		"renderer": RenderingServer.get_current_rendering_method(),
		"driver": RenderingServer.get_current_rendering_driver_name(),
		"display_server": DisplayServer.get_name(),
		"android_preferred": "Mobile Vulkan",
		"compatibility_available": true,
		"desktop_reference": "Forward+ optional",
		"ssr_ssao_gi_volumetric_fog_required": false,
		"mobile_fps_measured": false,
		"missing_material_surfaces": missing,
		"untextured_white_review": warnings,
	}, "\t"))
	print("Runtime audit materials missing=", missing, ", suspicious white=", warnings)
	quit(1 if missing > 0 else 0)


func inspect_mesh(building: String, lod: String, active: bool, mesh_label: String, mesh: Mesh,
		finish_override: Material, source: String, instance: MeshInstance3D) -> int:
	if mesh == null:
		missing += 1
		return 0
	for surface in mesh.get_surface_count():
		var material := finish_override
		if material == null and instance != null:
			material = instance.get_surface_override_material(surface)
		if material == null:
			material = mesh.surface_get_material(surface)
		var state := "bound"
		var label := material.resource_name if material != null else ""
		if material == null:
			missing += 1
			state = "missing_material"
		elif material is StandardMaterial3D:
			var pbr := material as StandardMaterial3D
			texture_binding(building,lod,mesh_label,surface,label,"albedo",pbr.albedo_texture)
			texture_binding(building,lod,mesh_label,surface,label,"normal",pbr.normal_texture)
			texture_binding(building,lod,mesh_label,surface,label,"roughness",pbr.roughness_texture)
			texture_binding(building,lod,mesh_label,surface,label,"ao",pbr.ao_texture)
			texture_binding(building,lod,mesh_label,surface,label,"metallic",pbr.metallic_texture)
			var color := pbr.albedo_color
			if pbr.albedo_texture == null and minf(minf(color.r,color.g),color.b) >= .98:
				state = "untextured_white_review"
				warnings += 1
		elif material is ShaderMaterial:
			var shader := material as ShaderMaterial
			for uniform in shader.shader.get_shader_uniform_list():
				var value: Variant = shader.get_shader_parameter(uniform.name)
				if value is Texture2D:
					texture_binding(building,lod,mesh_label,surface,label,uniform.name,value)
		runtime_csv.store_csv_line([building,lod,str(active),mesh_label,str(surface),
			str(finish_override != null),label,source,state])
	return mesh.get_surface_count()


func texture_binding(building: String, lod: String, node: String, surface: int, material: String,
		channel: String, texture: Texture2D) -> void:
	if texture == null:
		return
	var path := texture.resource_path
	var tokens := path.split("/")
	var id := tokens[-2] if tokens.size() > 2 else texture.resource_name
	if "/hdri/" in path:
		id = path.get_file().get_basename()
	binding_csv.store_csv_line([building,lod,node,str(surface),material,channel,id,path,
		str(texture.get_width()),str(texture.get_height())])
