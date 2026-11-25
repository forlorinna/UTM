extends Node3D

const SAVE_PATH := "user://campus.cfg"
const MAP_SCRIPT := preload("res://scripts/campus_map.gd")
const LANGUAGES := ["en", "zh_CN", "ms"]
const QUALITY := ["Performance", "Balanced", "High", "Ultra", "Photography"]

var site: CampusSite
var atmosphere: CampusAtmosphere
var life_sim: CampusLife
var explorer: CampusExplorer
var vehicle: Node3D
var map: CampusMap
var hud: CanvasLayer
var root: Control
var title: Label
var detail: Label
var mode: Label
var prompt: Label
var activity: Label
var settings: PanelContainer
var settings_stack: VBoxContainer
var settings_frame: VBoxContainer
var touch_controls: Control
var joystick: Control
var touch_left := -1
var touch_right := -1
var stick := Vector2.ZERO
var stick_origin := Vector2.ZERO
var ascend := false
var descend := false
var test_run := false
var photo := false
var quality := 1
var language := 0
var balance := 20
var checkins := 0
var study_sessions := 0
var toast_time := 0.0
var save_time := 0.0
var display_time := 0.0
var shift := false
var free_look := false


func _ready() -> void:
	test_run = OS.get_cmdline_user_args().has("--test") or OS.get_cmdline_user_args().has("--capture")
	site = CampusSite.new()
	add_child(site)
	explorer = CampusExplorer.new()
	explorer.site = site
	add_child(explorer)
	place_at_plaza()
	atmosphere = CampusAtmosphere.new()
	atmosphere.context = site
	add_child(atmosphere)
	life_sim = CampusLife.new()
	life_sim.site = site
	add_child(life_sim)
	if ResourceLoader.exists("res://scripts/sedan.gd"):
		var script: Script = load("res://scripts/sedan.gd")
		vehicle = script.new()
		vehicle.site = site
		add_child(vehicle)
	if not test_run:
		load_save()
	TranslationServer.set_locale(LANGUAGES[language])
	create_hud()
	set_quality(quality)
	atmosphere.update_world(0.0, explorer.lens.global_position, false, true)
	if not test_run and not OS.has_feature("mobile") and not OS.get_cmdline_user_args().has("--touch-ui"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		free_look = true
	if OS.get_cmdline_user_args().has("--capture"):
		capture.call_deferred()


func place_at_plaza() -> void:
	explorer.position = site.world_point(CampusSite.SPAWN, 0.24)
	explorer.velocity = Vector3.ZERO
	explorer.heading = -0.77
	explorer.pitch = .235


func _physics_process(dt: float) -> void:
	if explorer == null or hud == null:
		return
	if settings.visible:
		return
	var keyboard := Vector2(
		int(Input.is_physical_key_pressed(KEY_D)) - int(Input.is_physical_key_pressed(KEY_A)),
		int(Input.is_physical_key_pressed(KEY_S)) - int(Input.is_physical_key_pressed(KEY_W)))
	explorer.walk_input = (keyboard + stick).limit_length()
	explorer.rise_input = float((int(ascend or Input.is_physical_key_pressed(KEY_SPACE)))
		- int(descend or Input.is_physical_key_pressed(KEY_CTRL)))
	if explorer.driving and is_instance_valid(vehicle):
		vehicle.drive(dt, explorer.walk_input, Input.is_physical_key_pressed(KEY_SPACE) or ascend)
		explorer.global_position = vehicle.global_position + Vector3.UP * .23
		explorer.heading = vehicle.rotation.y
		explorer.update_camera()
	else:
		explorer.step(dt, Input.is_physical_key_pressed(KEY_SHIFT) or shift)
	if not explorer.indoor:
		site.set_lod(explorer.lens.global_position)


func _process(dt: float) -> void:
	if hud == null:
		return
	atmosphere.update_world(0.0 if settings.visible else dt, get_viewport().get_camera_3d().global_position, explorer.indoor)
	if not settings.visible and not test_run:
		save_time += dt
		if save_time > 10.0:
			save_time = 0.0
			write_save()
	life_sim.update_visitors(0.0 if settings.visible else dt, atmosphere.clock_minutes, atmosphere.rain_amount, get_viewport().get_camera_3d().global_position, explorer.indoor or photo)
	toast_time = maxf(0, toast_time - dt)
	activity.visible = toast_time > 0.0
	display_time += dt
	if display_time < 0.12:
		return
	display_time = 0.0
	refresh_hud()
	map.queue_redraw()


func _input(event: InputEvent) -> void:
	if root == null:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_ESCAPE, KEY_TAB:
				toggle_settings()
			KEY_M:
				if not settings.visible:
					toggle_map()
			KEY_F:
				if not settings.visible:
					explorer.toggle_flight()
			KEY_V:
				explorer.first_person = not explorer.first_person
			KEY_G:
				explorer.flight_gear = (explorer.flight_gear + 1) % 3
			KEY_R:
				if not settings.visible:
					interact()
			KEY_E:
				if not settings.visible:
					toggle_vehicle()
			KEY_C:
				if not settings.visible:
					toggle_photo()
			KEY_SPACE:
				if not settings.visible and not explorer.flying and not explorer.driving and explorer.is_on_floor():
					explorer.velocity.y = 5.6
	if settings.visible or map.expanded:
		return
	if event is InputEventMouseMotion and free_look and not explorer.driving:
		explorer.look(event.relative)
	if event is InputEventScreenTouch and touch_controls.visible:
		if not event.pressed:
			if event.index == touch_left:
				touch_left = -1
				stick = Vector2.ZERO
				joystick.hide()
			if event.index == touch_right:
				touch_right = -1
			return
		if event.position.y >= 110 and event.position.y < root.size.y - 82:
			if event.position.x < root.size.x * 0.40 and touch_left < 0:
				touch_left = event.index
				stick_origin = event.position
				joystick.position = stick_origin - joystick.size / 2
				joystick.show()
				get_viewport().set_input_as_handled()
			elif event.position.x >= root.size.x * .48 and touch_right < 0:
				touch_right = event.index
				get_viewport().set_input_as_handled()
	if event is InputEventScreenDrag:
		if event.index == touch_left:
			stick = ((event.position - stick_origin) / 61.0).limit_length()
			get_viewport().set_input_as_handled()
		if event.index == touch_right:
			if not explorer.driving:
				explorer.look(event.relative * 1.45)
			get_viewport().set_input_as_handled()


func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_CLOSE_REQUEST] and is_instance_valid(explorer) and not test_run:
		write_save()


func write_save() -> void:
	var cfg := ConfigFile.new()
	var stored_position := explorer.position
	if explorer.indoor or explorer.driving or explorer.flying:
		stored_position = site.world_point(CampusSite.SPAWN, .22)
	cfg.set_value("game", "schema", 1)
	cfg.set_value("game", "position", stored_position)
	cfg.set_value("game", "heading", explorer.heading)
	cfg.set_value("game", "pitch", explorer.pitch)
	cfg.set_value("game", "balance", balance)
	cfg.set_value("game", "checkins", checkins)
	cfg.set_value("game", "study", study_sessions)
	cfg.set_value("world", "minutes", atmosphere.clock_minutes)
	cfg.set_value("world", "clock_locked", atmosphere.clock_locked)
	cfg.set_value("world", "speed", atmosphere.speed_index)
	cfg.set_value("world", "weather", atmosphere.weather)
	cfg.set_value("world", "lightning", atmosphere.lightning_enabled)
	cfg.set_value("display", "quality", quality)
	cfg.set_value("display", "language", language)
	cfg.set_value("display", "first_person", explorer.first_person)
	cfg.set_value("display", "sensitivity", explorer.look_sensitivity)
	cfg.set_value("display", "invert", explorer.reverse_vertical)
	cfg.set_value("display", "audio", atmosphere.ambient_audio)
	cfg.set_value("display", "campus_crowd", life_sim.density)
	var tmp := SAVE_PATH + ".tmp"
	if cfg.save(tmp) == OK:
		DirAccess.rename_absolute(ProjectSettings.globalize_path(tmp), ProjectSettings.globalize_path(SAVE_PATH))


func load_save() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK or cfg.get_value("game", "schema", 0) != 1:
		return
	var at: Variant = cfg.get_value("game", "position", explorer.position)
	if at is Vector3 and at.is_finite() and CampusSite.SITE_LIMIT.has_point(Vector2(at.x, at.z)):
		explorer.position = site.world_point(Vector2(at.x, at.z), 0.24)
	explorer.heading = wrapf(read_number(cfg, "game", "heading", -.77), -PI, PI)
	explorer.pitch = clampf(read_number(cfg, "game", "pitch", .235), -1.51, 1.4)
	balance = clampi(int(read_number(cfg, "game", "balance", 20)), 0, 999999)
	checkins = clampi(int(read_number(cfg, "game", "checkins", 0)), 0, 999999)
	study_sessions = clampi(int(read_number(cfg, "game", "study", 0)), 0, 999999)
	quality = clampi(int(read_number(cfg, "display", "quality", 1)), 0, QUALITY.size() - 1)
	language = clampi(int(read_number(cfg, "display", "language", 0)), 0, LANGUAGES.size() - 1)
	atmosphere.weather = clampi(int(read_number(cfg, "world", "weather", 0)), 0, CampusAtmosphere.WEATHER.size() - 1)
	atmosphere.clock_minutes = fposmod(read_number(cfg, "world", "minutes", 908.0), 1440.0)
	atmosphere.clock_locked = read_bool(cfg,"world","clock_locked",true)
	atmosphere.speed_index = clampi(int(read_number(cfg, "world", "speed", 1)), 0, 3)
	atmosphere.lightning_enabled = read_bool(cfg, "world", "lightning", false)
	atmosphere.ambient_audio = read_bool(cfg, "display", "audio", true)
	life_sim.density = clampf(read_number(cfg, "display", "campus_crowd", .72), 0.0, 1.0)
	explorer.first_person = read_bool(cfg, "display", "first_person", true)
	explorer.reverse_vertical = read_bool(cfg, "display", "invert", false)
	explorer.look_sensitivity = clampf(read_number(cfg, "display", "sensitivity", .0028), .0008, .008)


func read_number(cfg: ConfigFile, group: String, name: String, fallback: float) -> float:
	var value: Variant = cfg.get_value(group, name, fallback)
	if value is int or (value is float and is_finite(value)):
		return float(value)
	return fallback


func read_bool(cfg: ConfigFile, group: String, name: String, fallback: bool) -> bool:
	var value: Variant = cfg.get_value(group, name, fallback)
	return value if value is bool else fallback


func near_plaza() -> bool:
	return Vector2(explorer.position.x, explorer.position.z).distance_to(CampusSite.PLAZA) < 13.0 and not explorer.flying and not explorer.driving


func enter_room() -> void:
	explorer.indoor = true
	explorer.flying = false
	explorer.driving = false
	explorer.position = CampusSite.ROOM + Vector3(0, .15, 4.5)
	explorer.heading = 0
	explorer.pitch = -.04
	explorer.velocity = Vector3.ZERO
	site.exterior.hide()
	site.interior.show()
	map.expanded = false
	map.hide()
	notify("Fictional reading room • R to return")


func leave_room() -> void:
	explorer.indoor = false
	explorer.position = site.world_point(CampusSite.PLAZA, .23)
	explorer.velocity = Vector3.ZERO
	explorer.heading = -.75
	explorer.pitch = .10
	site.exterior.show()
	site.interior.hide()
	if not photo:
		map.show()


func interact() -> void:
	if explorer.indoor:
		leave_room()
	elif near_plaza():
		enter_room()
	else:
		notify("Reading room access is at the Menara Razak forecourt")


func toggle_vehicle() -> void:
	if not is_instance_valid(vehicle) or explorer.indoor or explorer.flying:
		return
	if explorer.driving:
		if absf(vehicle.speed) > 0.65:
			notify("Brake before leaving the car")
			return
		explorer.driving = false
		explorer.player_body.disabled = false
		var passenger_side := vehicle.global_position + vehicle.global_basis.x * 1.68
		explorer.position = site.world_point(Vector2(passenger_side.x, passenger_side.z), .18)
	else:
		if explorer.position.distance_to(vehicle.global_position) > 4.8:
			notify("Walk up to the parked sedan")
			return
		explorer.player_body.disabled = true
		explorer.driving = true
		explorer.first_person = false
		explorer.pitch = -.10


func style_box(color: Color, border: Color, radius: int, margin: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = color
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(radius)
	style.content_margin_left = margin
	style.content_margin_right = margin
	style.content_margin_top = margin
	style.content_margin_bottom = margin
	return style


func copy_text(words: String, size_px: int, color := Color("#e5e7d8")) -> Label:
	var result := Label.new()
	result.text = words
	result.add_theme_font_size_override("font_size", size_px)
	result.add_theme_color_override("font_color", color)
	result.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return result


func ui_button(words: String, action: Callable) -> Button:
	var button := Button.new()
	button.text = words
	button.focus_mode = Control.FOCUS_NONE
	button.pressed.connect(action)
	return button


func pin(node: Control, at: Vector2, rectangle: Rect2) -> void:
	node.set_anchor(SIDE_LEFT, at.x)
	node.set_anchor(SIDE_RIGHT, at.x)
	node.set_anchor(SIDE_TOP, at.y)
	node.set_anchor(SIDE_BOTTOM, at.y)
	node.offset_left = rectangle.position.x
	node.offset_top = rectangle.position.y
	node.offset_right = rectangle.end.x
	node.offset_bottom = rectangle.end.y


func create_hud() -> void:
	hud = CanvasLayer.new()
	add_child(hud)
	root = Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(root)
	var theme := Theme.new()
	theme.default_font_size = 16
	theme.default_font = preload("res://assets/i18n/NotoSansSC-subset.otf")
	var border := Color(0.70,0.72,0.54,0.23)
	var backing := Color(0.06,0.105,0.10,0.91)
	theme.set_stylebox("panel", "PanelContainer", style_box(backing, border, 10, 12))
	theme.set_stylebox("normal", "Button", style_box(Color("#253733"), border, 7, 9))
	theme.set_stylebox("hover", "Button", style_box(Color("#365048"), border, 7, 9))
	theme.set_stylebox("pressed", "Button", style_box(Color("#4a5c4a"), border, 7, 9))
	root.theme = theme
	var header := PanelContainer.new()
	root.add_child(header)
	pin(header, Vector2.ZERO, Rect2(22, 18, 304, 84))
	header.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lines := VBoxContainer.new()
	header.add_child(lines)
	title = copy_text("Menara Razak", 25, Color("#f4e7c8"))
	detail = copy_text("", 15, Color("#c3d4c5"))
	lines.add_child(title)
	lines.add_child(detail)

	var actions := HBoxContainer.new()
	actions.name = "Actions"
	root.add_child(actions)
	pin(actions, Vector2(1,0), Rect2(-400, 18, 378, 46))
	actions.add_child(ui_button("Map  M", toggle_map))
	actions.add_child(ui_button("Zoom", zoom_map))
	actions.add_child(ui_button("Photo  C", toggle_photo))
	actions.add_child(ui_button("Settings  Esc", toggle_settings))
	map = MAP_SCRIPT.new()
	map.geography = site.campus
	map.clip_contents = true
	map.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(map)
	pin(map, Vector2(1,0), Rect2(-265, 82, 243, 184))

	var footer := PanelContainer.new()
	footer.name = "Footer"
	root.add_child(footer)
	pin(footer, Vector2(0,1), Rect2(22,-73,500,54))
	footer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var footer_line := VBoxContainer.new()
	footer.add_child(footer_line)
	mode = copy_text("", 16, Color("#f4e7c8"))
	prompt = copy_text("", 14, Color("#b5cbbf"))
	footer_line.add_child(mode)
	footer_line.add_child(prompt)
	activity = copy_text("", 19, Color("#f6dfb1"))
	activity.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(activity)
	pin(activity, Vector2(.5,1), Rect2(-370,-153,740,38))
	activity.hide()
	create_touch_controls()
	create_settings()


func create_touch_controls() -> void:
	touch_controls = Control.new()
	touch_controls.mouse_filter = Control.MOUSE_FILTER_IGNORE
	touch_controls.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(touch_controls)
	var buttons := HBoxContainer.new()
	touch_controls.add_child(buttons)
	pin(buttons, Vector2(1,1), Rect2(-494,-76,472,59))
	buttons.add_child(ui_button("Room", interact))
	buttons.add_child(ui_button("Car", toggle_vehicle))
	buttons.add_child(ui_button("View", func(): explorer.first_person = not explorer.first_person))
	buttons.add_child(ui_button("Fly", explorer.toggle_flight))
	var up := ui_button("▲", func(): pass)
	up.button_down.connect(func(): ascend = true)
	up.button_up.connect(func(): ascend = false)
	buttons.add_child(up)
	var down := ui_button("▼", func(): pass)
	down.button_down.connect(func(): descend = true)
	down.button_up.connect(func(): descend = false)
	buttons.add_child(down)
	joystick = Panel.new()
	joystick.mouse_filter = Control.MOUSE_FILTER_IGNORE
	joystick.add_theme_stylebox_override("panel", style_box(Color(0.19,0.25,0.22,.32), Color("#94b2a0"), 61, 0))
	joystick.size = Vector2(122,122)
	touch_controls.add_child(joystick)
	joystick.hide()
	update_touch_visibility()


func update_touch_visibility() -> void:
	touch_controls.visible = not photo and (OS.has_feature("mobile") or OS.get_cmdline_user_args().has("--touch-ui"))


func control_row(words: String) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	var property := copy_text(words, 16, Color("#d7e2cd"))
	property.custom_minimum_size.x = 151
	row.add_child(property)
	settings_stack.add_child(row)
	return row


func dropdown(row: HBoxContainer, labels: Array, selected: int, action: Callable) -> void:
	var selector := OptionButton.new()
	for item in labels:
		selector.add_item(str(item))
	selector.select(selected)
	selector.item_selected.connect(action)
	selector.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(selector)


func checkbox(row: HBoxContainer, enabled: bool, action: Callable) -> void:
	var toggle := CheckButton.new()
	toggle.button_pressed = enabled
	toggle.toggled.connect(action)
	row.add_child(toggle)


func create_settings() -> void:
	settings = PanelContainer.new()
	root.add_child(settings)
	pin(settings, Vector2(.5,.5), Rect2(-300,-326,600,652))
	settings_frame = VBoxContainer.new()
	settings_frame.add_theme_constant_override("separation", 11)
	settings.add_child(settings_frame)
	settings_frame.add_child(copy_text("UTMKL Campus Life", 28, Color("#f4e7c8")))
	settings_frame.add_child(copy_text("Independent offline campus sample", 15, Color("#b5cbbf")))
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	settings_frame.add_child(scroll)
	settings_stack = VBoxContainer.new()
	settings_stack.add_theme_constant_override("separation", 11)
	settings_stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(settings_stack)
	var row := control_row("Time in Kuala Lumpur")
	var hours := SpinBox.new()
	hours.max_value = 23
	hours.value = floorf(atmosphere.clock_minutes / 60)
	row.add_child(hours)
	var minutes := SpinBox.new()
	minutes.max_value = 59
	minutes.value = fmod(atmosphere.clock_minutes, 60.0)
	row.add_child(minutes)
	var lock := CheckButton.new()
	lock.text = "Lock"
	lock.button_pressed = atmosphere.clock_locked
	lock.toggled.connect(func(enabled): atmosphere.clock_locked = enabled)
	row.add_child(lock)
	var set_clock := func(_value):
		atmosphere.clock_minutes = hours.value * 60.0 + minutes.value
		lock.button_pressed = true
		atmosphere.update_world(0.0, explorer.lens.global_position, explorer.indoor, true)
	hours.value_changed.connect(set_clock)
	minutes.value_changed.connect(set_clock)
	dropdown(control_row("Time rate"), CampusAtmosphere.SPEEDS, atmosphere.speed_index, func(i): atmosphere.speed_index = i)
	dropdown(control_row("Weather"), CampusAtmosphere.WEATHER, atmosphere.weather, func(i):
		atmosphere.weather = i
		atmosphere.update_world(0.0, explorer.lens.global_position, explorer.indoor, true))
	dropdown(control_row("Graphics"), QUALITY, quality, set_quality)
	checkbox(control_row("Lightning flashes"), atmosphere.lightning_enabled, func(enabled): atmosphere.lightning_enabled = enabled)
	checkbox(control_row("Ambient audio"), atmosphere.ambient_audio, func(enabled): atmosphere.ambient_audio = enabled)
	checkbox(control_row("Invert vertical look"), explorer.reverse_vertical, func(enabled): explorer.reverse_vertical = enabled)
	var sensitivity := HSlider.new()
	sensitivity.min_value = 0.0008
	sensitivity.max_value = 0.008
	sensitivity.step = 0.0001
	sensitivity.value = explorer.look_sensitivity
	sensitivity.value_changed.connect(func(value): explorer.look_sensitivity = value)
	sensitivity.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	control_row("Look sensitivity").add_child(sensitivity)
	var crowd := HSlider.new()
	crowd.max_value = 1.0
	crowd.step = .1
	crowd.value = life_sim.density
	crowd.value_changed.connect(func(value): life_sim.density = value)
	crowd.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	control_row("Campus crowd").add_child(crowd)
	var quick := control_row("Visit")
	quick.add_child(ui_button("Forecourt", func():
		if explorer.indoor:
			leave_room()
		explorer.flying = false
		explorer.driving = false
		explorer.player_body.disabled = false
		place_at_plaza()
		toggle_settings()))
	quick.add_child(ui_button("Reading room", func():
		explorer.player_body.disabled = false
		enter_room()
		toggle_settings()))
	dropdown(control_row("Language"), ["English", "中文", "Bahasa Melayu"], language, func(i):
		language = i
		TranslationServer.set_locale(LANGUAGES[language]))
	var life := control_row("Campus activities")
	life.add_child(ui_button("Check in", func():
		if near_plaza():
			checkins += 1
			notify("Forecourt check-in saved")
		else:
			notify("Check in from the Menara Razak forecourt")))
	life.add_child(ui_button("Study / RM 3 snack", func():
		if explorer.indoor and balance >= 3:
			balance -= 3
			study_sessions += 1
			notify(tr("Study session saved · virtual RM %d") % balance)
		else:
			notify("Available in the fictional reading room with RM 3")))
	var resume := ui_button("Resume", toggle_settings)
	settings_frame.add_child(resume)
	settings.hide()


func set_quality(value: int) -> void:
	quality = clampi(value, 0, QUALITY.size() - 1)
	var viewport := get_viewport()
	if RenderingServer.get_current_rendering_method() != "gl_compatibility":
		viewport.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if quality >= 1 else Viewport.SCREEN_SPACE_AA_DISABLED
	viewport.msaa_3d = Viewport.MSAA_4X if quality >= 3 else (Viewport.MSAA_2X if quality == 2 else Viewport.MSAA_DISABLED)
	atmosphere.sun.shadow_enabled = quality > 0
	atmosphere.sun.directional_shadow_max_distance = [55.0, 127.0, 170.0, 230.0, 285.0][quality]


func notify(words: String) -> void:
	activity.text = words
	toast_time = 3.4


func toggle_settings() -> void:
	settings.visible = not settings.visible
	stick = Vector2.ZERO
	touch_left = -1
	touch_right = -1
	ascend = false
	descend = false
	joystick.hide()
	if not OS.has_feature("mobile") and not test_run:
		free_look = not settings.visible and not map.expanded
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if free_look else Input.MOUSE_MODE_VISIBLE
	if not test_run:
		write_save()


func toggle_map() -> void:
	if explorer.indoor:
		return
	map.expanded = not map.expanded
	if map.expanded:
		map.move_to_front()
		pin(map, Vector2(.5,.5), Rect2(-420,-270,840,540))
	else:
		pin(map, Vector2(1,0), Rect2(-265,82,243,184))
	free_look = not map.expanded and not OS.has_feature("mobile")
	if not test_run and not OS.has_feature("mobile"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if free_look else Input.MOUSE_MODE_VISIBLE
	map.queue_redraw()


func zoom_map() -> void:
	map.zoom = fposmod(map.zoom + .5, 1.5)
	map.queue_redraw()


func toggle_photo() -> void:
	photo = not photo
	for node in root.get_children():
		if (node is PanelContainer and node != settings) or (node.name == "Actions" and not OS.has_feature("mobile")):
			node.visible = not photo
	map.visible = not photo and not explorer.indoor
	update_touch_visibility()


func nearest_landmark(at: Vector2) -> String:
	var nearest := "UTM Kuala Lumpur"
	var distance := 133.0
	for landmark in site.campus.buildings:
		if landmark.asset.is_empty():
			continue
		var dist := at.distance_to(Vector2(landmark.x, landmark.z))
		if dist < distance:
			distance = dist
			nearest = "MJIIT" if landmark.id == "osm-way-733313948" else landmark.name
	return nearest


func refresh_hud() -> void:
	var world := explorer.global_position
	var planar := Vector2(world.x, world.z)
	title.text = "Fictional Reading Room" if explorer.indoor else nearest_landmark(planar)
	detail.text = "%s  ·  %s  ·  RM %d" % [atmosphere.time_label(), tr(CampusAtmosphere.WEATHER[atmosphere.weather]), balance]
	if explorer.flying:
		mode.text = tr("Flight %d  ·  %.0f m AGL  ·  %.0f m elevation") % [explorer.flight_gear + 1,
			world.y - site.ground_height(planar), world.y + site.campus.vertical_origin_m]
		prompt.text = "WASD move  ·  Space/Ctrl climb/descend  ·  G speed  ·  F land"
	elif explorer.driving:
		mode.text = tr("Driving  ·  %.0f km/h  ·  Keep left") % (absf(vehicle.speed) * 3.6)
		prompt.text = "WASD steer and reverse  ·  Space brake  ·  E exit"
	else:
		mode.text = "Reading room" if explorer.indoor else "Walk  ·  Offline sample"
		prompt.text = "R return outside" if explorer.indoor else ("R reading room  ·  E drive  ·  F fly" if near_plaza()
			else "WASD walk  ·  Shift run  ·  E enter sedan  ·  F fly")
	if touch_controls.visible and not explorer.indoor:
		prompt.text = "Hold ▲/▼ to climb or descend" if explorer.flying else ("Use the stick to steer · ▲ to brake" if explorer.driving else "Move: left touch  ·  Look: right drag")
	map.player_at = planar
	map.heading = explorer.heading


func capture() -> void:
	var args := OS.get_cmdline_user_args()
	var at := args.find("--capture")
	var out := args[at + 1] if at + 1 < args.size() else "/tmp"
	var views := args[at + 2] if at + 2 < args.size() else "day"
	set_physics_process(false)
	var camera := Camera3D.new()
	add_child(camera)
	camera.current = true
	for view in views.split(",", false):
		var code: Error = await capture_view(out, view, camera)
		if code != OK:
			get_tree().quit(code)
			return
	get_tree().quit()


func capture_view(out: String, view: String, camera: Camera3D) -> Error:
	if explorer.indoor:
		leave_room()
	atmosphere.weather = 0
	atmosphere.clock_minutes = 908.0
	var eye := site.world_point(Vector2(-66, 72), 2.15)
	var target := Vector3(10, 19.5, 2)
	if view == "night":
		atmosphere.clock_minutes = 1213.0
	elif view == "rain":
		atmosphere.clock_minutes = 1060.0
		atmosphere.weather = 4
	elif view == "aerial":
		eye = Vector3(-97, 110, 95)
		target = Vector3(27, 8, -54)
	elif view == "roof":
		eye = Vector3(-54, 68, 57)
		target = Vector3(15, 39, 6)
	elif view == "residensi":
		eye = Vector3(372, 92, 209)
		target = Vector3(253, 26, 93)
	elif view == "masjid":
		eye = Vector3(156, 19, 224)
		target = Vector3(105, -1, 166)
	elif view == "mjiit":
		eye = site.world_point(Vector2(49, 55), 1.80)
		target = Vector3(125, 10.0, 44)
	elif view == "entry":
		eye = site.world_point(Vector2(-23, 27), 1.76)
		target = Vector3(-1, -0.2, 12)
	elif view == "interior":
		enter_room()
		eye = CampusSite.ROOM + Vector3(6.4, 1.68, 4.8)
		target = CampusSite.ROOM + Vector3(-2.4, 1.68, -3.3)
	hud.visible = view == "hud"
	set_quality(2 if view == "hud" else 3)
	atmosphere.update_world(0.0, eye, explorer.indoor, true)
	camera.global_position = eye
	camera.fov = 53 if view != "interior" else 67
	camera.look_at(target, Vector3.UP)
	camera.current = true
	site.set_lod(eye)
	for frame in 6:
		await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var code := image.save_png(out + "/utmkl-" + view + ".png")
	print("Captured ", view, " with LOD", site.lod, "; result ", code)
	return code
