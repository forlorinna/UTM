class_name CampusLife
extends Node3D

const SAM := preload("res://assets/people/sam.glb")
const MAYA := preload("res://assets/people/maya.glb")
const ROUTES := [
	[Vector2(-33, 22), Vector2(-27, 18), Vector2(-23, 20), Vector2(-22, 24), Vector2(-31, 25)],
	[Vector2(-14, 36), Vector2(-17, 32), Vector2(-27, 28), Vector2(-32, 24), Vector2(-23, 31)],
	[Vector2(70.9, 12), Vector2(71.4, 31), Vector2(71.9, 52), Vector2(72, 70), Vector2(71.9, 49)],
	[Vector2(80, 55), Vector2(91, 51), Vector2(102, 48), Vector2(98, 47), Vector2(88, 46)],
	[Vector2(-50, 39), Vector2(-48, 41), Vector2(-43, 50), Vector2(-52, 58), Vector2(-55, 52)],
]
var site: CampusSite
var visitors: Array[Node3D] = []
var animation_players: Array[AnimationPlayer] = []
var route_index: Array[int] = []
var wait_time: Array[float] = []
var density := 0.72
var ticker := 0.0


func _ready() -> void:
	for i in ROUTES.size():
		var pivot := Node3D.new()
		pivot.name = "Visitor_%d" % (i + 1)
		add_child(pivot)
		var model := ((SAM if i % 2 == 0 else MAYA).instantiate()) as Node3D
		pivot.add_child(model)
		model.rotation.y = PI
		var animation := model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
		var name := "Walk_Relaxed" if i % 2 == 0 else "Walk_Carry"
		if animation.has_animation(name):
			animation.get_animation(name).loop_mode = Animation.LOOP_LINEAR
			animation.play(name, -1, .84 + (i % 3) * .08)
			animation.seek(i * .28, true)
		animation_players.append(animation)
		visitors.append(pivot)
		route_index.append(1)
		wait_time.append(0.0)
		pivot.position = site.world_point(ROUTES[i][0], .09)


func update_visitors(dt: float, clock_minutes: float, rain: float, eye: Vector3, hidden: bool) -> void:
	var lunchtime := smoothstep(645.0, 760.0, clock_minutes) * (1.0 - smoothstep(860.0, 1020.0, clock_minutes))
	var awake := smoothstep(415.0, 505.0, clock_minutes) * (1.0 - smoothstep(1080.0, 1200.0, clock_minutes))
	var count := ceili(visitors.size() * density * awake * (.66 + lunchtime*.34) * (1.0 - rain*.6))
	for i in visitors.size():
		var npc := visitors[i]
		var active := i < count and not hidden and npc.position.distance_to(eye) < 130.0
		npc.visible = active
		var animation := animation_players[i]
		if not active:
			animation.speed_scale = 0.0
			continue
		var route: Array = ROUTES[i]
		var target: Vector2 = route[route_index[i]]
		var current := Vector2(npc.position.x, npc.position.z)
		if wait_time[i] > 0.0:
			wait_time[i] -= dt
			animation.speed_scale = 0.0
			continue
		if current.distance_to(target) <= .09:
			route_index[i] = (route_index[i] + 1) % route.size()
			wait_time[i] = .7 + (i + route_index[i]) % 3
			continue
		var heading := -atan2(target.x - current.x, -(target.y - current.y))
		npc.rotation.y = lerp_angle(npc.rotation.y, heading, minf(1.0, dt * 5.5))
		var toward := current.move_toward(target, dt * (1.29 + (i % 3)*.12))
		npc.position = site.world_point(toward, .09)
		animation.speed_scale = 1.0
