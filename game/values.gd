extends Node

var uri = -1
var empty = true
var _vals_linear = {}
var _vals_ease =   {}
var _vals_ease_out =   {}
var _vals_step =   {}
var _vals_target = {}
var _vals_start =  {}

func _ready():
	pass

func _process(delta: float):
	for name in _vals_linear.keys():
		_linear_add(name, _vals_step[name] * delta * 10)
	for name in _vals_ease.keys():
		_ease_add(name, _vals_step[name] * delta * 10)
	for name in _vals_ease_out.keys():
		_ease_out_add(name, _vals_step[name] * delta * 10)

func add_val_linear(name, start_val, target_val, step = 1):
	_vals_linear[name] = start_val
	_vals_target[name] = target_val
	_vals_step[name] = step
	_vals_start[name] = start_val
	empty = false
	
func add_val_ease(name, start_val, target_val, step = 0.5):
	_vals_ease[name] = start_val
	_vals_target[name] = target_val
	_vals_step[name] = step
	_vals_start[name] = start_val
	empty = false

func add_val_ease_out(name, start_val, target_val, step = 0.5):
	_vals_ease_out[name] = start_val
	_vals_target[name] = target_val
	_vals_step[name] = step
	_vals_start[name] = start_val
	empty = false

func get_target_val(name):
	if _vals_target.has(name):
		return _vals_target[name]
	return null

func change_target_val(name, new_target_val):
	_vals_target[name] = new_target_val
	_vals_start[name] = gett(name)

func has(name):
	return _vals_linear.has(name) or _vals_ease.has(name) or _vals_ease_out.has(name)

func gett(name):
	if _vals_linear.has(name):
		return _vals_linear[name]
	if _vals_ease.has(name):
		return _vals_ease[name]
	if _vals_ease_out.has(name):
		return _vals_ease_out[name]
	return 0

func sett(name, val):
	if _vals_linear.has(name):
		_vals_linear[name] = val
	elif _vals_ease.has(name):
		_vals_ease[name] = val
	elif _vals_ease_out.has(name):
		_vals_ease_out[name] = val
	_vals_start[name] = val

func _linear_add(name, step):
	var target = _vals_target[name]
	var sgn = 1 if _vals_start[name] < target else -1
	if _vals_linear[name] != target:
		_vals_linear[name] += step * sgn
		if sgn * (target - _vals_linear[name]) < 1e-8:
			_vals_linear[name] = target

func _ease_add(name, step):
	var target = _vals_target[name]
	var sgn = 1 if _vals_start[name] < target else -1
	if _vals_ease[name] != target:
		_vals_ease[name] += ((target - _vals_ease[name]) if sgn > 0 else (_vals_ease[name] - _vals_start[name] + 0.1 * sgn)) * step
		if sgn * (target - _vals_ease[name]) < 1e-8:
			_vals_ease[name] = target

func _ease_out_add(name, step):
	var target = _vals_target[name]
	var sgn = 1 if _vals_start[name] < target else -1
	if _vals_ease_out[name] != target:
		_vals_ease_out[name] += ((target - _vals_ease_out[name]) if sgn <= 0 else (_vals_ease_out[name] - _vals_start[name] + 0.1 * sgn)) * step
		if sgn * (target - _vals_ease_out[name]) < 1e-8:
			_vals_ease_out[name] = target

func toggle_val(name, off = 0, on = 1):
	if _vals_target.has(name):
		if _vals_target[name] == on:
			change_target_val(name, off)
			return false
		change_target_val(name, on)
		return true
	return false
