extends SceneTree

var failures := 0


func _initialize() -> void:
	run.call_deferred()


func check(passed: bool, description: String) -> void:
	if not passed:
		failures += 1
	print(("PASS " if passed else "FAIL ") + description)


func run() -> void:
	var game: Node = load("res://scenes/campus.tscn").instantiate()
	root.add_child(game)
	var site: CampusSite = game.site
	var player: CampusExplorer = game.explorer
	var sky: CampusAtmosphere = game.atmosphere
	var car: CharacterBody3D = game.vehicle
	game.set_process(false)
	game.set_physics_process(false)
	for _frame in 12:
		await physics_frame
		player.step(1.0/60, false)
	check(site.campus.buildings.size() == 71 and site.campus.roads.size() == 160, "offline mapped campus inventory")
	check(site.exterior.get_child_count() >= 72 and site.road.albedo_texture != null and site.road.normal_texture != null,
		"terrain chunks, roads and scanned PBR channels")
	check(player.is_on_floor(), "player rests on terrain collision")
	check(player.animation.has_animation("Walk_Relaxed") and player.animation.has_animation("Run"), "skinned player walk and run clips")
	check(game.life_sim.visitors.size() == 5 and game.life_sim.animation_players[1].has_animation("Walk_Carry"),
		"pooled campus people and phone-carry walk animation")

	var labels := [site.tower, site.mjiit]
	for landmark in site.southeast:
		labels.append(landmark.node)
	for building in labels:
		for level in 3:
			var scene: Node3D = building.get_node("LOD%d" % level)
			var meshes := scene.find_children("*", "MeshInstance3D", true, false)
			var valid := not meshes.is_empty()
			for asset in meshes:
				for index in asset.mesh.get_surface_count():
					valid = valid and asset.mesh.surface_get_material(index) != null
			check(valid, "%s LOD%d imports with assigned materials" % [building.name, level])
		check(not building.find_children("*", "CollisionShape3D", true, false).is_empty(), "%s has an independent collision mesh" % building.name)
	var heights := [20, 50, 150, 300]
	var expected := [0, 0, 1, 2]
	for i in heights.size():
		var eye := Vector3(8, site.tower.position.y + heights[i], 14)
		site.set_lod(eye)
		check(site.lod == expected[i] and site.tower.get_node("LOD%d" % expected[i]).visible,
			"Menara LOD%d at %d m above base" % [expected[i], heights[i]])

	var start := player.position
	player.walk_input = Vector2(0,-1)
	for _frame in 24:
		await physics_frame
		player.step(1.0/60, false)
	check(player.position.distance_to(start) > .15, "ground walking integrates movement")
	player.walk_input = Vector2.ZERO
	player.toggle_flight()
	player.rise_input = 1.0
	var lift_start := player.position.y
	for _frame in 18:
		await physics_frame
		player.step(1.0/60, false)
	check(player.flying and player.position.y > lift_start + .4, "airborne ascend with collision-based control")
	player.toggle_flight()
	player.rise_input = 0
	check(not player.flying, "flight exits to gravity")

	game.enter_room()
	sky.weather = 4
	sky.update_world(0, player.global_position, player.indoor, true)
	check(site.interior.visible and not site.exterior.visible and not sky.rain.emitting, "room portal suppresses exterior geometry and rain")
	game.leave_room()
	sky.update_world(0, player.global_position, player.indoor, true)
	check(sky.rain.emitting and sky.wetness > .8 and site.exterior.visible, "outdoor downpour enables rain and wet surfaces")

	player.position = car.position + Vector3(2.1,0,0)
	game.toggle_vehicle()
	check(player.driving and player.player_body.disabled and car.rollers.size() == 4, "vehicle entry and four axle pivots")
	var parked := car.position
	for _frame in 34:
		await physics_frame
		car.drive(1.0/60, Vector2(0,-1), false)
	check(car.speed > .7 and car.position.distance_to(parked) > .15 and absf(car.wheel_roll) > .01, "vehicle throttle, motion and rotating wheels")
	for _frame in 32:
		await physics_frame
		car.drive(1.0/60, Vector2.ZERO, true)
	game.toggle_vehicle()
	check(not player.driving and not player.player_body.disabled and absf(car.speed) < .65, "vehicle brake and exit")

	sky.clock_minutes = 1420
	sky.clock_locked = true
	sky.update_world(25, player.position,false)
	check(sky.clock_minutes == 1420 and sky.daylight < .05, "locked late-night time remains fixed")
	sky.clock_locked = false
	sky.speed_index = 3
	sky.update_world(30, player.position,false)
	check(is_equal_approx(sky.clock_minutes, 10), "60× automatic clock wraps midnight")
	game.balance = 17
	game.quality = 3
	game.language = 2
	game.write_save()
	game.balance = 1
	game.quality = 0
	game.language = 0
	sky.weather = 0
	game.load_save()
	check(game.balance == 17 and game.quality == 3 and game.language == 2 and sky.weather == 4, "restore save schema, balance, weather, quality and language")
	var file := FileAccess.open("user://campus.cfg", FileAccess.WRITE)
	file.store_string("[invalid")
	file.close()
	game.load_save()
	check(game.balance == 17, "corrupt save preserves active state")
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://campus.cfg"))
	check(not TranslationServer.get_loaded_locales().is_empty(), "Godot locale resources are loaded")

	print("Automated runtime failures: ", failures)
	quit(0 if failures == 0 else 1)
