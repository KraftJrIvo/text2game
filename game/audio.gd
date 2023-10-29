class_name AudioSource
extends Node

const POOL_SZ = 10

@export var volume = 1.0

var _audio_players = []
var players_by_inst = {}

func _ready():
	pass

func _allocate_player(snd_vol = 1.0):
	var audio_player = AudioStreamPlayer3D.new()
	#audio_player.pause_mode = Node.PAUSE_MODE_PROCESS
	audio_player.doppler_tracking = false
	audio_player.volume_db = snd_vol * volume
	get_parent().add_child(audio_player)
	audio_player.global_transform.origin = get_parent().global_transform.origin
	#var dist = 0audio_player.global_transform.origin.distance_to(global.get_player_cam().global_transform.origin)
	#if dist < 1.1:
	#	audio_player.vol *= 0.5
	audio_player.unit_size = linear_to_db(audio_player.volume_db)
	if len(_audio_players) < POOL_SZ:
		_audio_players.append(audio_player)
	elif _audio_players.count(null) > 0:
		_audio_players[_audio_players.find(null)] = audio_player
	return audio_player

func _dispose_of_players():
	for i in len(_audio_players):
		if _audio_players[i] and not _audio_players[i].playing:
			_audio_players[i] = null

func play_sound(sound, vol = 1.0):
	var audio_player = _allocate_player(vol)
	if audio_player:
		audio_player.stream = sound
		audio_player.play()
		_dispose_of_players()

func _reloop_sound(ap):
	ap.play()

func loop_sound(inst_id, snd_id, snd, vol = 1.0):
	var has_inst = players_by_inst.has(inst_id)
	var has_snd = has_inst and players_by_inst[inst_id].has(snd_id)
	if not has_inst or not has_snd:
		var audio_player = _allocate_player(vol)
		if audio_player:
			audio_player.stream = snd
			audio_player.play()
			audio_player.connect('finished', _reloop_sound.bind(audio_player))
			if not has_inst:
				players_by_inst[inst_id] = {}
			players_by_inst[inst_id][snd_id] = audio_player
			return audio_player

func stop_loop(inst_id, snd_id):
	if players_by_inst.has(inst_id) and players_by_inst[inst_id].has(snd_id):
		var player = players_by_inst[inst_id][snd_id]
		if player:
			player.disconnect('finished', _reloop_sound.bind(player))
			players_by_inst[inst_id].erase(snd_id)
			var id = _audio_players.find(player)
			if _audio_players.find(player) >= 0:
				_audio_players[id].stop()
				_audio_players[id] = null

func update_volume():
	for ap in _audio_players:
		if ap != null:
			ap.unit_db = linear_to_db(ap.volume_db)
