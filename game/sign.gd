class_name Sign
extends StaticBody3D

var title: String = "Test"
var text: String = "testtesttest"

var time = 0

func _ready():
	pass

func _process(delta):
	time += delta
	$sprite.position.y = 4 + sin(time)
