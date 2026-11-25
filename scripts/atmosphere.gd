class_name CampusAtmosphere
extends Node3D

const WEATHER := ["Clear", "Partly cloudy", "Overcast", "Showers", "Downpour", "Thunderstorm", "After rain"]
const RAIN_AMOUNT := [0.0, 0.0, 0.0, 0.45, 0.93, 1.0, 0.0]
const CLOUD_AMOUNT := [0.05, 0.35, 0.86, 0.78, 0.98, 1.0, 0.50]
const WET_AMOUNT := [0.0, 0.0, 0.06, 0.62, 0.95, 1.0, 0.79]
const SPEEDS := [1, 10, 30, 60]
const LAND := "res://assets/polyhaven/"
const SKY_NAMES := ["kloofendal_48d_partly_cloudy_puresky", "overcast_soil_puresky"]

var clock_minutes := 908.0
var clock_locked := true
var speed_index := 1
var weather := 0
var wetness := 0.0
var cloudy := 0.0
var rain_amount := 0.0
var lightning_enabled := false
var daylight := 1.0
var ambient_audio := true
var flash := 0.0
var thunder_delay := 9.0
var context: CampusSite
var environment := Environment.new()
var sun := DirectionalLight3D.new()
var rain := CPUParticles3D.new()
var panoramas: Array[PanoramaSkyMaterial] = []
var rain_sound: AudioStreamPlayer
var birds_sound: AudioStreamPlayer


func _ready() -> void:
	environment.background_mode = Environment.BG_SKY
	environment.sky = Sky.new()
	environment.sky.radiance_size = Sky.RADIANCE_SIZE_128
	environment.sky.process_mode = Sky.PROCESS_MODE_QUALITY
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	for id in SKY_NAMES:
		var panorama := PanoramaSkyMaterial.new()
		panorama.panorama = load(LAND + id + "/" + id + "_2k.hdr")
		panoramas.append(panorama)
	environment.sky.sky_material = panoramas[0]
	var world := WorldEnvironment.new()
	world.environment = environment
	add_child(world)
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 145.0
	sun.shadow_bias = 0.09
	add_child(sun)
	build_rain()
	rain_sound = ambience("res://assets/audio/rain.ogg")
	birds_sound = ambience("res://assets/audio/birds.ogg")


func ambience(path: String) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	if ResourceLoader.exists(path):
		var clip := load(path) as AudioStreamOggVorbis
		clip.loop = true
		player.stream = clip
		player.volume_db = -80.0
		add_child(player)
		if DisplayServer.get_name() != "headless" and not OS.get_cmdline_user_args().has("--capture"):
			player.play()
	return player


func build_rain() -> void:
	rain.emitting = false
	rain.amount = 490
	rain.lifetime = 0.58
	rain.local_coords = false
	rain.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	rain.emission_box_extents = Vector3(10, 2.0, 10)
	rain.initial_velocity_min = 12.0
	rain.initial_velocity_max = 22.0
	rain.direction = Vector3(0.28, -1, 0.13)
	rain.gravity = Vector3(1.4, -17, 0)
	rain.spread = 6.0
	rain.scale_amount_min = 0.7
	rain.scale_amount_max = 1.3
	var streak := QuadMesh.new()
	streak.size = Vector2(0.017, 0.39)
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = Color(0.70, 0.79, 0.86, 0.29)
	streak.material = material
	rain.mesh = streak
	rain.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(rain)


func update_world(dt: float, eye: Vector3, indoors: bool, snap := false) -> void:
	if not clock_locked:
		clock_minutes = fposmod(clock_minutes + dt * SPEEDS[speed_index] / 60.0, 1440.0)
	var blend := 1.0 if snap else 1.0 - exp(-dt * 0.46)
	wetness = lerpf(wetness, WET_AMOUNT[weather], blend)
	cloudy = lerpf(cloudy, CLOUD_AMOUNT[weather], blend)
	rain_amount = lerpf(rain_amount, RAIN_AMOUNT[weather], blend)
	var phase := (clock_minutes - 425.0) * TAU / 1440.0
	var height_angle := sin(phase)
	daylight = smoothstep(-0.12, 0.23, height_angle)
	if lightning_enabled and weather == 5 and not indoors:
		thunder_delay -= dt
		if thunder_delay <= 0.0:
			flash = 0.38
			thunder_delay = randf_range(10.0, 22.0)
	flash = move_toward(flash, 0, dt * 0.7)
	var warm := daylight * (1.0 - smoothstep(0.04, 0.6, height_angle))
	# Geographic orientation uses equatorial daylight and approximate equinox angles.
	var solar_dir := Vector3(cos(phase), maxf(height_angle, .05), 0.32).normalized()
	sun.look_at(sun.global_position - solar_dir, Vector3.UP)
	sun.light_color = Color("#fff6e8").lerp(Color("#ffb375"), warm * 0.65)
	sun.light_energy = 1.05 * daylight * (1.0 - cloudy * .79) + flash
	sun.visible = not indoors
	var sky_index := 1 if cloudy >= 0.59 else 0
	if environment.sky.sky_material != panoramas[sky_index]:
		environment.sky.sky_material = panoramas[sky_index]
	environment.background_energy_multiplier = lerpf(0.023, 0.92, daylight) * (1.0 - cloudy * .23) + flash
	environment.ambient_light_color = Color("#445678").lerp(Color("#d4e2f5"), daylight).lerp(Color("#e9d7c1"), warm*.32)
	environment.ambient_light_energy = 0.11 if indoors else lerpf(.15, .57, daylight) + flash
	environment.fog_enabled = not indoors and (rain_amount > .07 or cloudy > .68)
	environment.fog_light_color = Color("#22314a").lerp(Color("#c6d9e6"), daylight)
	environment.fog_density = 0.0007 + rain_amount * .0051
	environment.fog_sky_affect = 0.17
	rain.global_position = eye + Vector3(0, 8, 0)
	rain.mesh.material.albedo_color = Color(0.70, 0.79, 0.86, rain_amount * 0.37)
	rain.emitting = rain_amount > .04 and not indoors and eye.y < 95.0
	if rain_sound.stream != null:
		rain_sound.volume_db = linear_to_db(maxf(0.0001, rain_amount * (.08 if indoors else .42))) if ambient_audio else -80.0
	if birds_sound.stream != null:
		birds_sound.volume_db = linear_to_db(maxf(.0001, .18 * daylight * (1.0 - rain_amount))) if ambient_audio and not indoors else -80.0
	context.road.albedo_color = Color("#939696").lerp(Color("#5e6267"), wetness*.72)
	context.road.roughness = lerpf(1.0, 0.47, wetness)
	context.road.metallic_specular = lerpf(.30, .70, wetness)
	for mat in context.night_panels:
		mat.emission_energy_multiplier = (1.0 - daylight) * .58
	for lamp in context.street_lights:
		lamp.light_energy = (1.0 - daylight) * 3.2
		lamp.visible = daylight < .95


func time_label() -> String:
	return "%02d:%02d" % [int(clock_minutes) / 60, int(clock_minutes) % 60]
