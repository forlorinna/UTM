extends CharacterBody3D

const MODEL := preload("res://assets/vehicles/sedan.glb")
const PARKING := Vector2(-48.8, 47.4)
const WHEEL_RADIUS := 0.334
var site: CampusSite
var speed := 0.0
var steer := 0.0
var wheel_roll := 0.0
var front_axles: Array[Node3D] = []
var rollers: Array[Node3D] = []


func _ready() -> void:
	name = "CampusSedan"
	position = site.world_point(PARKING, .055)
	rotation.y = -.54
	floor_snap_length = .46
	floor_max_angle = deg_to_rad(40)
	var chassis := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.78, 1.11, 4.52)
	chassis.shape = shape
	chassis.position.y = .60
	add_child(chassis)
	var body := MODEL.instantiate() as Node3D
	body.rotation.y = -PI / 2
	add_child(body)
	for wheel_id in ["FrontLeft", "FrontRight", "RearLeft", "RearRight"]:
		var wheel := body.find_child(wheel_id, true, false) as Node3D
		var pivot := Node3D.new()
		pivot.name = wheel_id + "Axle"
		body.add_child(pivot)
		pivot.global_position = wheel.global_position
		var roller := Node3D.new()
		pivot.add_child(roller)
		wheel.reparent(roller, true)
		rollers.append(roller)
		if wheel_id.begins_with("Front"):
			front_axles.append(pivot)


func drive(dt: float, command: Vector2, brake: bool) -> void:
	var target_speed := -command.y * (8.3 if command.y <= 0 else 3.5)
	if brake:
		target_speed = 0.0
	var acceleration := 13.0 if brake else (3.9 if absf(command.y) > .05 else 2.15)
	speed = move_toward(speed, target_speed, dt * acceleration)
	steer = move_toward(steer, command.x, dt * 3.4)
	rotation.y -= dt * speed * steer * 0.22
	var motion := -transform.basis.z * speed
	velocity.x = motion.x
	velocity.z = motion.z
	velocity.y = -1.2 if is_on_floor() else velocity.y - 18.0 * dt
	move_and_slide()
	for i in get_slide_collision_count():
		var impact := get_slide_collision(i)
		if absf(impact.get_normal().y) < .49:
			speed *= .34
	if not CampusSite.SITE_LIMIT.has_point(Vector2(position.x, position.z)) or position.y < -27.0:
		position = site.world_point(PARKING, .055)
		rotation.y = -.54
		speed = 0.0
	wheel_roll = wrapf(wheel_roll + speed * dt / WHEEL_RADIUS, -PI, PI)
	for roller in rollers:
		roller.rotation.z = wheel_roll
	for pivot in front_axles:
		pivot.rotation.y = -steer * .46
