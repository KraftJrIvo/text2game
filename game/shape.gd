class_name ShapE
extends StaticBody3D

var mesh_path : String
var size : float = 0
var angle : float = 0

func _ready():
	$mesh.mesh = load(mesh_path)
	$mesh.mesh.surface_set_material(0, StandardMaterial3D.new())
	$mesh.mesh.surface_get_material(0).vertex_color_use_as_albedo = true
	$mesh.scale = Vector3.ONE * size / 2.0
	$mesh.rotate_y(angle)
	var r = sqrt(size / 2.0)
	$mesh.position.y += r - 0.5
	$col.shape.radius = r

func _process(delta):
	pass
