class_name CampusExplorer
extends CharacterBody3D

const WALK_SPEED := 3.4
const FLY_SPEEDS := [8.0, 19.0, 42.0]
var lens := Camera3D.new()
var first_person := true
var flying := false
var flight_gear := 1
var heading := 0.0
var pitch := -0.15
var look_sensitivity := 0.0028
var reverse_vertical := false
var indoor := false
var driving := false
var site: CampusSite
var walk_input := Vector2.ZERO
var rise_input := 0.0
var player_body: CollisionShape3D
var avatar: Node3D
var animation: AnimationPlayer


func _ready() -> void:
	floor_snap_length = 0.32
	floor_max_angle = deg_to_rad(48.0)
	player_body = CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = .29
	capsule.height = 1.65
	player_body.shape = capsule
	player_body.position.y = 0.83
	add_child(player_body)
	add_child(lens)
	lens.fov = 69
	lens.near = .08
	lens.far = 1100.0
	lens.current = true
	avatar = CampusLife.SAM.instantiate() as Node3D
	add_child(avatar)
	avatar.rotation.y = PI
	animation = avatar.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	for clip in ["Walk_Relaxed", "Run"]:
		if animation.has_animation(clip):
			animation.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	if animation.has_animation("Walk_Relaxed"):
		animation.play("Walk_Relaxed")
		animation.seek(.15, true)
		animation.pause()


func look(delta: Vector2) -> void:
	heading = wrapf(heading - delta.x * look_sensitivity, -PI, PI)
	var vertical := -1.0 if reverse_vertical else 1.0
	pitch = clampf(pitch - delta.y * look_sensitivity * vertical, -1.51, 1.40)


func update_camera() -> void:
	rotation.y = heading
	avatar.visible = not first_person and not driving
	lens.rotation.x = pitch
	var eye := global_position + Vector3.UP * 1.64
	lens.global_position = eye
	if first_person:
		return
	var offset := global_transform.basis * (Basis(Vector3.RIGHT, pitch) * Vector3(0, .25, 4.6 if not driving else 6.4))
	var query := PhysicsRayQueryParameters3D.create(eye, eye + offset)
	query.exclude = [get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		lens.global_position = eye + offset
	else:
		lens.global_position = eye + offset.normalized() * maxf(0.0, eye.distance_to(hit.position) - .18)


func step(dt: float, running: bool) -> void:
	var desired := (Basis(Vector3.UP, heading) * Vector3(walk_input.x, 0, walk_input.y)).limit_length(1.0)
	if flying:
		velocity = desired * FLY_SPEEDS[flight_gear]
		velocity.y = rise_input * FLY_SPEEDS[flight_gear] * .68
		if global_position.y >= 315.0:
			velocity.y = minf(velocity.y, 0)
	else:
		if is_on_floor() and velocity.y <= 0.0:
			velocity.y = -0.5
		else:
			velocity.y -= 18.5 * dt
		var speed := WALK_SPEED * (1.56 if running else 1.0)
		velocity.x = move_toward(velocity.x, desired.x * speed, dt * 26.0)
		velocity.z = move_toward(velocity.z, desired.z * speed, dt * 26.0)
	move_and_slide()
	if not first_person:
		animate_avatar(desired, running)
	if not indoor:
		position.x = clampf(position.x, CampusSite.SITE_LIMIT.position.x, CampusSite.SITE_LIMIT.end.x)
		position.z = clampf(position.z, CampusSite.SITE_LIMIT.position.y, CampusSite.SITE_LIMIT.end.y)
		if position.y < -27.0:
			position = site.world_point(CampusSite.SPAWN, .2)
			velocity = Vector3.ZERO
	update_camera()


func animate_avatar(direction: Vector3, running: bool) -> void:
	if flying or direction.length_squared() < .012:
		animation.pause()
		return
	var next_clip := "Run" if running else "Walk_Relaxed"
	if not animation.has_animation(next_clip):
		return
	var world_yaw := -atan2(direction.x, -direction.z)
	avatar.rotation.y = lerp_angle(avatar.rotation.y, PI + world_yaw - heading, .19)
	if animation.current_animation != next_clip or not animation.is_playing():
		animation.play(next_clip, .17, 1.25 if running else 1.38)


func toggle_flight() -> void:
	if indoor or driving:
		return
	flying = not flying
	if flying:
		position.y += .25
	velocity = Vector3.ZERO
