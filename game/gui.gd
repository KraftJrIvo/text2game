extends Control

func _ready():
	pass

func _process(delta):
	pass

func _on_ok_pressed():
	$sign_popup.visible = false
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	get_parent().play_sign_sound()
