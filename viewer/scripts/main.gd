extends Node3D
# ============================================================
# main.gd - Segelphysik-Viewer
# Empfaengt UDP/JSON vom Bridge (Port 9999): Pose, Kraftpfeile
# (prim = durchgezogen, gegen = GLEICHE FARBE gestrichelt),
# Stroemungspfeile, HUD. Eingaben gehen an Port 9998 zurueck.
# ============================================================

const PORT := 9999
const PORT_CMD := 9998
const PFEIL_SKALA := {"vertikal": 0.12, "seiten": 1.5}  # m pro kN je Gruppe

const FARBE := {
	"vertikal": Color(0.25, 0.55, 1.0),
	"seiten": Color(0.15, 0.85, 0.35),
}

var udp: PacketPeerUDP
var cmd_udp: PacketPeerUDP
var yacht: Node3D
var pfeile := {}
var etikett := {}
var flow_mm: MultiMeshInstance3D
var flow_max := 64
var rw := 0.0
var fm := 1200.0
var send_acc := 0.0
var hud: Label
var cam_node: Camera3D
var wasser_node: MeshInstance3D
var bridge_label: Label
var letzte_pkt_ms: int = -1000000

func _ready() -> void:
	udp = PacketPeerUDP.new()
	if udp.bind(PORT) != OK:
		push_error("UDP-Port %d belegt?" % PORT)
	cmd_udp = PacketPeerUDP.new()
	_baue_umgebung()
	_baue_yacht()
	_baue_fluss()
	_baue_hud()

func _baue_umgebung() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.55, 0.75, 0.90)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.75, 0.82, 0.90)
	env.ambient_light_energy = 0.75
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sonne := DirectionalLight3D.new()
	sonne.rotation_degrees = Vector3(-55, 30, 0)
	sonne.light_energy = 1.2
	add_child(sonne)
	var cam := Camera3D.new()
	cam.set_script(load("res://scripts/orbit_cam.gd"))
	add_child(cam)
	cam_node = cam
	cam.make_current()
	var wasser := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(140, 140)
	plane.subdivide_width = 60
	plane.subdivide_depth = 60
	wasser.mesh = plane
	var wm := ShaderMaterial.new()
	wm.shader = load("res://shaders/water.gdshader")
	wasser.material_override = wm
	add_child(wasser)
	wasser_node = wasser

func _hull_mat(c: Color) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/hull.gdshader")
	m.set_shader_parameter("dry", c)
	m.set_shader_parameter("wet", c.darkened(0.5))
	return m

func _baue_yacht() -> void:
	yacht = Node3D.new()
	add_child(yacht)
	var hull := MeshInstance3D.new()
	if ResourceLoader.exists("res://yacht_hull.obj"):
		hull.mesh = load("res://yacht_hull.obj")
		hull.rotation_degrees = Vector3(-90, 0, 0)
	else:
		var box := BoxMesh.new()
		box.size = Vector3(9, 1.6, 2.96)
		hull.mesh = box
	hull.material_override = _hull_mat(Color(0.85, 0.72, 0.50))
	yacht.add_child(hull)
	var keel := MeshInstance3D.new()
	if ResourceLoader.exists("res://yacht_keel.obj"):
		keel.mesh = load("res://yacht_keel.obj")
		keel.rotation_degrees = Vector3(-90, 0, 0)
	else:
		var box2 := BoxMesh.new()
		box2.size = Vector3(1.0, 1.6, 0.3)
		box2.position = Vector3(0, -1.4, 0)
		keel.mesh = box2
	keel.material_override = _hull_mat(Color(0.30, 0.32, 0.38))
	yacht.add_child(keel)

func _baue_fluss() -> void:
	flow_mm = MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var box := BoxMesh.new()
	box.size = Vector3(0.035, 1.0, 0.035)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.30, 0.95, 1.00)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	box.material = mat
	mm.mesh = box
	mm.instance_count = flow_max
	flow_mm.multimesh = mm
	add_child(flow_mm)

func _baue_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	hud = Label.new()
	hud.position = Vector2(12, 10)
	hud.add_theme_font_size_override("font_size", 15)
	layer.add_child(hud)
	bridge_label = Label.new()
	bridge_label.position = Vector2(12, 104)
	bridge_label.add_theme_font_size_override("font_size", 13)
	layer.add_child(bridge_label)

func _pfeil_neu(farbe: Color, gestrichelt: bool) -> Node3D:
	var root := Node3D.new()
	var mat := StandardMaterial3D.new()
	mat.albedo_color = farbe
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if gestrichelt:
		for i in range(6):
			var seg := MeshInstance3D.new()
			var cyl := CylinderMesh.new()
			cyl.height = 0.10
			cyl.top_radius = 0.022
			cyl.bottom_radius = 0.022
			seg.mesh = cyl
			seg.material_override = mat
			seg.position.y = 0.08 + i * 0.155
			root.add_child(seg)
	else:
		var schaft := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.height = 1.0
		cyl.top_radius = 0.022
		cyl.bottom_radius = 0.022
		schaft.mesh = cyl
		schaft.material_override = mat
		schaft.position.y = 0.5
		root.add_child(schaft)
	var spitze := MeshInstance3D.new()
	var cone := CylinderMesh.new()
	cone.height = 0.20
	cone.top_radius = 0.0
	cone.bottom_radius = 0.065
	spitze.mesh = cone
	spitze.material_override = mat
	spitze.position.y = 1.10
	root.add_child(spitze)
	add_child(root)
	return root

func _pfeil_setzen(a: Node3D, p0: Vector3, d: Vector3, laenge: float) -> void:
	var sichtbar := laenge > 0.03 and d.length() > 1e-4
	a.visible = sichtbar
	if not sichtbar:
		return
	var dn: Vector3 = d.normalized()
	a.position = p0
	var xb := dn.cross(Vector3.UP)
	if xb.length() < 0.01:
		xb = dn.cross(Vector3.RIGHT)
	xb = xb.normalized()
	var zb: Vector3 = xb.cross(dn).normalized()
	a.basis = Basis(xb, dn, zb)
	a.scale = Vector3(1, laenge, 1)

func _empfangen() -> void:
	while udp.get_available_packet_count() > 0:
		var data = JSON.parse_string(udp.get_packet().get_string_from_utf8())
		if data == null:
			continue
		letzte_pkt_ms = Time.get_ticks_msec()
		if data.has("pose"):
			var po = data["pose"]
			var pos := Vector3(po["pos"][0], po["pos"][1], po["pos"][2])
			var qt = po["quat"]
			var quat := Quaternion(qt[0], qt[1], qt[2], qt[3])
			yacht.transform = Transform3D(Basis(quat), pos)
			if cam_node != null:
				cam_node.set("ziel", pos)
		if data.has("forces"):
			_kraefte_zeichnen(data["forces"])
		if data.has("flow"):
			_fluss_zeichnen(data["flow"])
		if data.has("stats"):
			var st = data["stats"]
			hud.text = "Fahrt   %.2f m/s  (%.1f kn)\nAbdrift %+.1f deg   Kraengung %+.1f deg\nBilanz  %.0f N   Ruder %+.0f deg   F_Segel %.0f N\nMaus: Kamera | Pfeile L/R: Ruder | PgUp/PgDn: Kraft | R: Reset" % [
				st["fahrt"], st["kn"], st["drift"], st["roll"],
				st["bilanz"], st["rw"], st["fm"]]

func _kraefte_zeichnen(forces: Array) -> void:
	var gesehen := {}
	for f in forces:
		var name: String = f["name"]
		gesehen[name] = true
		if not pfeile.has(name):
			var gr: String = f.get("gruppe", "seiten")
			var farbe: Color = FARBE.get(gr, Color.WHITE)
			var gestrichelt: bool = f.get("rolle", "prim") == "gegen"
			pfeile[name] = _pfeil_neu(farbe, gestrichelt)
			var lbl := Label3D.new()
			lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			lbl.no_depth_test = true
			lbl.font_size = 36
			lbl.pixel_size = 0.004
			lbl.modulate = farbe
			lbl.outline_size = 8
			add_child(lbl)
			etikett[name] = lbl
		var p: Vector3 = Vector3(f["p"][0], f["p"][1], f["p"][2])
		var fv := Vector3(f["F"][0], f["F"][1], f["F"][2])
		var betrag := fv.length()
		var skala: float = float(PFEIL_SKALA.get(f.get("gruppe", "seiten"), 1.5))
		var laenge: float = minf(skala * betrag / 1000.0, 6.0)
		_pfeil_setzen(pfeile[name], p, fv, laenge)
		var lbl2: Label3D = etikett[name]
		lbl2.visible = laenge > 0.03
		lbl2.text = "%s\n%.0f N" % [name, betrag]
		if betrag > 1e-4:
			lbl2.position = p + fv.normalized() * (laenge + 0.3)
		else:
			lbl2.position = p
	for name in pfeile.keys():
		if not gesehen.has(name):
			pfeile[name].visible = false
			etikett[name].visible = false

func _fluss_zeichnen(flow: Array) -> void:
	var mm: MultiMesh = flow_mm.multimesh
	var n: int = min(flow.size(), flow_max)
	for i in range(flow_max):
		if i < n:
			var fp = flow[i]
			var p: Vector3 = Vector3(fp["p"][0], fp["p"][1], fp["p"][2])
			var u: Vector3 = Vector3(fp["u"][0], fp["u"][1], fp["u"][2])
			var L: float = clampf(u.length() * 0.5, 0.05, 1.4)
			var dn: Vector3 = u.normalized() if u.length() > 1e-4 else Vector3.UP
			var xb := dn.cross(Vector3.UP)
			if xb.length() < 0.01:
				xb = Vector3.RIGHT
			xb = xb.normalized()
			var zb: Vector3 = xb.cross(dn).normalized()
			var b: Basis = Basis(xb, dn, zb).scaled(Vector3(1, L, 1))
			mm.set_instance_transform(i, Transform3D(b, p + dn * L * 0.5))
		else:
			var b0: Basis = Basis.IDENTITY.scaled(Vector3.ONE * 0.0001)
			mm.set_instance_transform(i, Transform3D(b0, Vector3(0, -99, 0)))

func _eingabe(delta: float) -> void:
	var geaendert := false
	if Input.is_key_pressed(KEY_LEFT):
		rw = clamp(rw - 60.0 * delta, -35.0, 35.0)
		geaendert = true
	if Input.is_key_pressed(KEY_RIGHT):
		rw = clamp(rw + 60.0 * delta, -35.0, 35.0)
		geaendert = true
	if Input.is_key_pressed(KEY_PAGEUP):
		fm = clamp(fm + 500.0 * delta, 0.0, 4000.0)
		geaendert = true
	if Input.is_key_pressed(KEY_PAGEDOWN):
		fm = clamp(fm - 500.0 * delta, 0.0, 4000.0)
		geaendert = true
	send_acc += delta
	if geaendert or send_acc > 0.5:
		send_acc = 0.0
		cmd_udp.set_dest_address("127.0.0.1", PORT_CMD)
		cmd_udp.put_packet(JSON.stringify({"rw_deg": rw, "fm": fm}).to_utf8_buffer())
	if Input.is_key_pressed(KEY_R):
		cmd_udp.set_dest_address("127.0.0.1", PORT_CMD)
		cmd_udp.put_packet(JSON.stringify({"cmd": "reset"}).to_utf8_buffer())

func _process(delta: float) -> void:
	_empfangen()
	_eingabe(delta)
	if wasser_node != null and yacht != null:
		wasser_node.position = Vector3(yacht.position.x, 0.0, yacht.position.z)
	if bridge_label != null:
		var alter := (Time.get_ticks_msec() - letzte_pkt_ms) / 1000.0
		if alter < 0.5:
			bridge_label.text = "Bridge: OK (%.0f Hz)" % (1.0 / max(delta, 0.001))
			bridge_label.modulate = Color(0.3, 1.0, 0.3)
		else:
			bridge_label.text = "Bridge: OFFLINE seit %.1f s" % alter
			bridge_label.modulate = Color(1.0, 0.35, 0.35)
