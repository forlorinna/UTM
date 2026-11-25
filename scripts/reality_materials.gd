class_name RealityMaterials
extends RefCounted

const ROOT := "res://assets/runtime/materials/"
const GRASS_SHADER := preload("res://assets/runtime/shaders/campus_ground.gdshader")


static func surface(id: String, tint: Color, uv_scale: Vector2, normal_strength: float, metal := 0.0) -> StandardMaterial3D:
	var source := ROOT + id + "/"
	var surface_material := StandardMaterial3D.new()
	surface_material.resource_name = "PolyHaven/" + id
	surface_material.set_meta("photographic_asset_id", id)
	surface_material.albedo_color = tint
	surface_material.albedo_texture = load(source + "albedo.jpg")
	surface_material.normal_enabled = true
	surface_material.normal_texture = load(source + "normal.png")
	surface_material.normal_scale = normal_strength
	surface_material.roughness_texture = load(source + "roughness.jpg")
	surface_material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	surface_material.roughness = 0.93
	surface_material.metallic = metal
	var ao_path := source + "ao.jpg"
	if ResourceLoader.exists(ao_path):
		surface_material.ao_enabled = true
		surface_material.ao_texture = load(ao_path)
		surface_material.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	surface_material.uv1_scale = Vector3(uv_scale.x, uv_scale.y, 1)
	surface_material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return surface_material


static func terrain_layer() -> ShaderMaterial:
	var material := ShaderMaterial.new()
	material.resource_name = "Photographic Turf and Broad Ground"
	material.shader = GRASS_SHADER
	material.set_shader_parameter("turf_color", load(ROOT + "leafy_grass/albedo.jpg"))
	material.set_shader_parameter("turf_normal", load(ROOT + "leafy_grass/normal.png"))
	material.set_shader_parameter("turf_roughness", load(ROOT + "leafy_grass/roughness.jpg"))
	material.set_shader_parameter("broad_color", load(ROOT + "aerial_grass_rock/albedo.jpg"))
	material.set_shader_parameter("broad_normal", load(ROOT + "aerial_grass_rock/normal.png"))
	material.set_shader_parameter("broad_roughness", load(ROOT + "aerial_grass_rock/roughness.jpg"))
	return material
