class_name Player
extends CharacterBody3D

const G =            20
const G_SMALL =      5
const FALL_SPD_LMT = 15
const JMP_H =        7
const SPD_LOW =      2
const SPD_WLK =      4
const SPD_RUN =      7
const ACC_DFT =      10
const ACC_AIR =      7
const ACC_CAM =      40
const HEAD_Y_DFT =   1.5
const HEAD_Y_LOW =   0.8
const ON_FLOOR_BUF = 3
const JUMP_BUF =     10
const PUSH =         0.25
const THROW_STR =    2.0
const MOUS_SENS =    0.3
const LVL_DEATH_BOTTOM = -50

var uri = -1
var human_name = ""
var dead        = false
var interpolate = true
var vel =      Vector3.ZERO
var mov =      Vector3.ZERO
var real_mov = Vector3.ZERO
var steps_mod =  null
var cur_lvl = null
var is_holding_dobj =     false
var is_moving =           false
var is_rotating =         false
var is_grabbing =         false
var was_grabbing =        false
var is_sprinting =        false
var is_crouching =        false
var is_jumping =          false
var is_throwing =         false
var is_picking_up =       false
var is_pointing_at_dobj = false
var is_pointing_at_act =  false
var is_pressing_act =     false
var _wind_sound = null
var crouching = false
var _running =   false
var _temp_fov =       0
var _crouch_cld =     0
var _has_jumped =     0
var _last_floor_y =   0
var _vel_y =          0
var _head_bob_coeff = 0
var _path_len =       0
var _prev_snd_id =    0
var _step_cd =        0
var _acc =          ACC_DFT
var _was_on_floor = ON_FLOOR_BUF
var _target_cam_h = HEAD_Y_DFT
var _cur_spd =      SPD_WLK
var _last_floor_normal = Vector3.UP
var _look_at_obj = null

@onready var prv_pos = global_transform.origin
#@onready var grabber = $grabber
@onready var head =    $head
@onready var camera =  $head/camera

func _ready():
	$values.add_val_ease("spdcff", 0, 0, 0.7)
	$values.add_val_ease_out("spdcff2", 0, 0, 0.7)

func _process(delta):
	is_holding_dobj = false
	var head_bob = _head_bob_coeff * _get_head_bob()
	camera.top_level = true
	if interpolate:
		camera.global_transform.origin = camera.global_transform.origin.lerp(head.global_transform.origin + Vector3.UP * head_bob, ACC_CAM * delta)
	else:
		camera.global_transform.origin = head.global_transform.origin + Vector3.UP * head_bob
	camera.rotation.y = rotation.y
	camera.rotation.x = head.rotation.x
	camera.rotation.z = 0
	interpolate = true

func _input(event):
	if Input.is_action_just_pressed("cam_lock"):
		was_grabbing = false
		is_grabbing = true
	is_throwing = Input.is_action_just_pressed("throw")# and $grabber.dobj
	if is_throwing:
		was_grabbing = true
	if Input.is_action_just_released("cam_lock"):
		was_grabbing = false
	if is_throwing or Input.is_action_just_released("cam_lock"):
		is_grabbing = false
	is_sprinting = Input.is_action_pressed("sprint")
	is_crouching = Input.is_action_pressed("crouch") or _crouch_cld > 0
	if _crouch_cld > 0:
		_crouch_cld -= 1
	is_jumping = Input.is_action_just_pressed("jump")
	is_rotating = event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED
	if is_rotating:
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
		rotate_y(deg_to_rad(-event.relative.x * MOUS_SENS))
		var delta = deg_to_rad(-event.relative.y * MOUS_SENS)
		if (delta > 0 and rad_to_deg(head.rotation.x + delta) < 89.9) or (delta < 0 and rad_to_deg(head.rotation.x + delta) > -89.9):
			head.rotate_x(delta)

func slerp_angle(from, to, weight):
	return from + short_angle_dist(from, to) * weight

func short_angle_dist(from, to):
	var max_angle = PI * 2
	var difference = fmod(to - from, max_angle)
	return fmod(2 * difference, max_angle) - difference
	
func _get_head_bob():
	return (sin(_path_len) + 1.0) * 0.1

func _physics_process(delta):
	_doRunLogic()
	_doJumpLogic()
	_doCrouchLogic()
	_doMovement(delta)

func _getWalkDir():
	var h_rot = global_transform.basis.get_euler().y
	var f_input = Input.get_action_strength("move_backward") - Input.get_action_strength("move_forward")
	var h_input = Input.get_action_strength("move_right") - Input.get_action_strength("move_left")
	is_moving = f_input != 0 or h_input != 0
	var A = Vector3(h_input, 0, f_input).rotated(Vector3.UP, h_rot).normalized()
	var B = _last_floor_normal
	var dir2 = B.cross(A.cross(B) / B.length())/B.length() if _was_on_floor > 0 else A # accounting for slopes
	return dir2

func _crouch(down = true):
	if not down or $hitbox_crouch.disabled:
		crouching = down
		$hitbox.disabled = down
		$hitbox_crouch.disabled = not down
		_target_cam_h = HEAD_Y_LOW if down else HEAD_Y_DFT
		if _was_on_floor <= 0:
			global_transform.origin.y += (HEAD_Y_DFT - HEAD_Y_LOW) * (1 if down else -1)
			head.position.y = _target_cam_h        
		if not down:
			var _o_ = move_and_collide(Vector3.UP * 0.01)

func stop_movement():
	vel = Vector3.ZERO
	mov = Vector3.ZERO
	real_mov = Vector3.ZERO
	_vel_y = 0
	_temp_fov = 0
	$values.sett("spdcff", 0)
	$values.sett("spdcff2", 0)

func _doMovement(delta):
	_vel_y += (G if (not is_on_wall() or _vel_y < 0 or _vel_y > 1.0) else G_SMALL) * delta
	if _vel_y > FALL_SPD_LMT:
		_vel_y = FALL_SPD_LMT
	_acc = ACC_DFT if _was_on_floor > 0 else ACC_AIR
	vel = vel.lerp(_getWalkDir() * _cur_spd, _acc * delta)
	mov = vel + Vector3.DOWN * _vel_y
	
	prv_pos = global_transform.origin
	
	move_and_slide()
	velocity = mov
	var _o_ = move_and_slide()
	#for index in range(get_slide_collision_count()):
	#	var collision = get_slide_collision(index)
	#	if collision.get_collider().is_in_group("dobj"):
	##		collision.get_collider().apply_central_impulse(-collision.normal * PUSH)
	#		if collision.get_collider() == $grabber.dobj:
	#			is_grabbing = false
	real_mov = global_transform.origin - prv_pos

	if is_on_wall():
		vel.x = real_mov.x / delta
		vel.z = real_mov.z / delta
				
	if is_on_floor():
		_last_floor_normal = get_floor_normal()
		_last_floor_y = global_transform.origin.y
		if _vel_y > 6:
			#_play_step_sound(true, false)
			get_parent().play_random_step()
		_was_on_floor = ON_FLOOR_BUF
	
	if is_on_ceiling():
		_vel_y = 0
	
	var mov_len = real_mov.length()
	if abs(_vel_y) < 1.0 and mov_len > 0.015:
		_path_len += mov_len * (2.0 if is_sprinting else 2.5) / 2.0

	var stepped = false	
	if crouching:
		_head_bob_coeff = 0
	else:
		if is_moving:
			_head_bob_coeff =  clamp(_head_bob_coeff + ((1.0 - _head_bob_coeff) / 1.1* delta * 10.0), 0, 1.0)
			if _was_on_floor > 0 and mov_len < 1.0 and mov_len > 0.02:
				_step_cd -= 1
				if _get_head_bob() < 0.01:
					#_play_step_sound(is_sprinting and mov_len > 0.1, true)
					get_parent().play_random_step()
					stepped = true
		else:
			_head_bob_coeff =  clamp(_head_bob_coeff - (_head_bob_coeff / 1.1 * delta * 10.0), 0, 1.0)
	if not stepped:
		steps_mod = null
	
	$values.change_target_val("spdcff", 1.0 if mov_len > 0.01 else 0.0)
	$values.change_target_val("spdcff2", 1.0 if sqrt(real_mov.x * real_mov.x + real_mov.z * real_mov.z) > 0.1 else 0.0)
	_temp_fov = clamp($values.gett("spdcff2") * 10, 0, 10)
	
	if is_on_floor() or (is_on_wall() and abs(global_transform.origin.y - _last_floor_y) < 0.01):
		_vel_y = 0
	else:
		_was_on_floor -= 1

func _doJumpLogic():
	if Input.is_action_just_pressed("jump"):
		_has_jumped = JUMP_BUF
	else:
		_has_jumped -= 1
		
	if _has_jumped > 0 and _was_on_floor > 0:
		get_parent().play_random_step()
		_vel_y = -JMP_H

func _doRunLogic():
	_running = is_sprinting and not crouching
	if _was_on_floor > 0:
		_cur_spd = SPD_RUN if _running else SPD_WLK
	if crouching:
		_cur_spd = SPD_LOW

func _doCrouchLogic():
	head.position.y += (_target_cam_h - head.position.y) * 0.33
	if is_crouching:
		_crouch()
	elif $hitbox.disabled:
		var space_state = get_world_3d().direct_space_state
		var off = 0.3 * Vector3.FORWARD.rotated(Vector3.UP, rotation.y)
		var off2 = off.rotated(Vector3.UP, -PI/4.0)
		var org = global_transform.origin
		var result1 = space_state.intersect_ray(PhysicsRayQueryParameters3D.create(org + off, org + Vector3.UP * 2.0 + off, 0xFFFFFFFF, [self]))
		var result2 = space_state.intersect_ray(PhysicsRayQueryParameters3D.create(org - off, org + Vector3.UP * 2.0 - off, 0xFFFFFFFF, [self]))
		var result3 = space_state.intersect_ray(PhysicsRayQueryParameters3D.create(org + off2, org + Vector3.UP * 2.0 + off2, 0xFFFFFFFF, [self]))
		var result4 = space_state.intersect_ray(PhysicsRayQueryParameters3D.create(org - off2, org + Vector3.UP * 2.0 - off2, 0xFFFFFFFF, [self]))
		if not result1 and not result2 and not result3 and not result4:
			_crouch(false)

func get_cam_dir():
	if Input.is_action_pressed("cam_lock"):
		return camera.project_ray_normal(get_viewport().get_global_mouse_position())
	return -camera.global_transform.basis.z

func choose_random_from(sz, except = -1):
	if sz > 0:
		if except > -1:
			return (except + randi_range(1, sz - 1)) % sz
		return randi_range(0, sz - 1 )
	return null

func _play_step_sound(loud : bool, cd : bool):
	pass
	#if cd and _step_cd > 0:
	#	return
	#var r = choose_random_from(3, _prev_snd_id)
	#var new_snd_id = r + (3 if loud else 0)
	#_prev_snd_id = r
	#var steps_src = steps_mod if steps_mod != null else global.get_current_level()
	#$audio.play_sound(steps_src.get_step(new_snd_id))
	#if cd:
	#	_step_cd = 20
