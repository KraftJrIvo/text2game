extends Node3D

const REACH = 1.0

const Sign_ = preload("res://Sign.tscn")
const Entrance_ = preload("res://Entrance.tscn")
const ShapE_ = preload("res://ShapE.tscn")

@export var world: String = "test1"
@export var start_area: int = 0

var cur_area = start_area
var active_object = null
var colors = null

var sign_sound = null
var enter_sound = null
var step_sounds = []

func load_img(area_dir, path):
	return ImageTexture.create_from_image(Image.load_from_file(area_dir + '/' + path))

func clear_objects():
	for c in $objects.get_children():
		c.queue_free()

func read_namedesc(area_dir, path):
	var file_text = FileAccess.get_file_as_string(area_dir + '/' + path)
	var lines = file_text.split('\n')
	var title = lines[0]
	lines.remove_at(0)
	var desc = '\n'.join(lines)
	return [title, desc]
	
func read_colors(area_dir, path):
	var file_text = FileAccess.get_file_as_string(area_dir + '/' + path)
	var lines = file_text.split('\n')
	return [Color(lines[0]), Color(lines[1])]

func spawn_sign(pos, tex, title, text):
	var sign = Sign_.instantiate()
	sign.get_node('sprite').texture = tex
	sign.title = title.substr(0, 40) if (len(title) > 40) else title
	sign.text = text
	$objects.add_child(sign)
	sign.global_position = pos

func spawn_entrance(pos, tex, area_idx):
	var entrance = Entrance_.instantiate()
	entrance.get_node('sprite').texture = tex
	entrance.area_idx = area_idx
	$objects.add_child(entrance)
	entrance.global_position = pos

func spawn_shape(pos, meshspath, size, angle):
	var shape = ShapE_.instantiate()
	shape.mesh_path = meshspath
	shape.size = size
	shape.angle = angle
	$objects.add_child(shape)
	shape.global_position = pos

func spawn_objects(area_dir, center):
	var file_text = FileAccess.get_file_as_string(area_dir + '/objects.txt')
	var lines = file_text.split('\n')
	for l in lines:
		var parts = l.split(' ')
		if len(parts) > 1:
			var pos = center + Vector3(float(parts[1]), 0, float(parts[2])) * $ground/mesh.scale.x / 2
			if parts[0] == 'sign':
				var namedesc = read_namedesc(area_dir, parts[3])
				spawn_sign(pos, load_img(area_dir, '../../sign.png'), namedesc[0], namedesc[1])
			elif parts[0] == 'entrance':
				spawn_entrance(pos, load_img(area_dir, '../' + parts[3] + '/entrance.png'), int(parts[3]))
			elif parts[0] == 'shape':
				pos.y += int(parts[4]) / 3.5 - 0.25
				spawn_shape(pos, area_dir + '/' + parts[3], int(parts[4]), float(parts[5]))

func switch_area(idx: int):
	active_object = null
	$player/audio.stop_loop(0, cur_area)
	clear_objects()
	var center = $player.global_position
	$ground.global_position = center
	var area_dir = "res://worlds/" + world + "/areas/" + str(idx)
	$ground/mesh.get_active_material(0).albedo_texture = load_img(area_dir, 'floor.png')
	$player/head/camera.environment.sky.sky_material.panorama = load_img(area_dir, 'panorama.png')
	cur_area = idx
	$player/audio.loop_sound(0, cur_area, load(area_dir + '/ambient.wav'), 1.1)
	enter_sound = load(area_dir + '/enter.wav')
	step_sounds = []
	for f in dir_contents(area_dir + '/steps'):
		step_sounds.append(load(area_dir + '/steps/' + f))
	spawn_objects(area_dir, center)

func dir_contents(path):
	var files = []
	var dir = DirAccess.open(path)
	if dir:
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if not dir.current_is_dir() and not file_name.ends_with('.import'):
				files.append(file_name)
			file_name = dir.get_next()
	else:
		print("An error occurred when trying to access the path.")
	return files

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	var world_dir = "res://worlds/" + world
	colors = read_colors(world_dir, "colors.txt")
	$gui/sign_popup.get_theme_stylebox("panel").texture = load_img(world_dir, "ui.png")
	$gui/sign_popup.get_theme_stylebox("panel").modulate_color = colors[0]
	var font = load(world_dir + "/font.otf")
	$gui/sign_popup/vbox/title.add_theme_font_override("font", font)
	$gui/sign_popup/vbox/title.add_theme_font_size_override("font_size", 40)
	$gui/sign_popup/vbox/title.add_theme_color_override("font_color", colors[1])
	$gui/sign_popup/vbox/title.add_theme_constant_override("outline_size", 5)
	$gui/sign_popup/vbox/title.add_theme_color_override("font_outline_color", Color.BLACK)
	$gui/sign_popup/vbox/text.add_theme_font_override("normal_font", font)
	$gui/sign_popup/vbox/text.add_theme_font_size_override("normal_font_size", 28)
	$gui/sign_popup/vbox/text.add_theme_color_override("default_color", colors[1])
	$gui/sign_popup/vbox/text.add_theme_color_override("font_outline_color", Color.BLACK)
	$gui/sign_popup/vbox/text.add_theme_constant_override("outline_size", 5)
	$gui/sign_popup/vbox/ok.add_theme_font_override("font", font)
	$gui/sign_popup/vbox/ok.add_theme_font_size_override("font_size", 28)
	$gui/sign_popup/vbox/ok.add_theme_color_override("font_color", colors[1])
	$gui/sign_popup/vbox/ok.add_theme_constant_override("outline_size", 5)
	$gui/sign_popup/vbox/ok.add_theme_color_override("font_outline_color", Color.BLACK)	
	sign_sound = load(world_dir + '/sign.wav')
	switch_area(cur_area)

func check_active_object():
	var new_active_object = null
	var space_state = get_world_3d().direct_space_state
	var from = $player/head/camera.global_position
	var to = from - REACH * $player/head/camera.global_transform.basis.z
	var query = PhysicsRayQueryParameters3D.create(from, to, 4294967295, [$player, $ground])
	var result = space_state.intersect_ray(query)
	if result and (not result.collider is ShapE):
		new_active_object = result.collider
		#$dbg.global_position = result.position
	if active_object and not new_active_object:
		active_object.get_node("sprite").modulate = Color.WHITE
	active_object = new_active_object
	if active_object:
		active_object.get_node("sprite").modulate = colors[1]

func play_random_step():
	$player/audio.play_sound(step_sounds.pick_random(), 1.1)

func play_sign_sound():
	$player/audio.play_sound(sign_sound, 1.1)

func do_stuff_with_active_object():
	if active_object is Sign:
		var sign : Sign = active_object
		Input.mouse_mode = Input.MOUSE_MODE_CONFINED
		$gui/sign_popup.visible = true
		$gui/sign_popup/vbox/title.text = sign.title
		$gui/sign_popup/vbox/text.text = sign.text
		play_sign_sound()
	elif active_object is Entrance:
		switch_area(active_object.area_idx)
		$player/audio.play_sound(enter_sound, 1.1)


func _process(delta):
	check_active_object()
	if Input.is_action_just_pressed('use'):
		do_stuff_with_active_object()
	if Input.is_action_just_pressed('esc'):
		switch_area(0)
