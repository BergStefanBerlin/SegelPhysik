extends Camera3D
# Orbit-Kamera: Linke Maustaste ziehen = drehen, Mausrad = zoomen.

var ziel := Vector3(0.0, -0.5, 0.0)
var dist := 14.0
var azim := 0.7
var elev := 0.35

func _unhandled_input(e: InputEvent) -> void:
    if e is InputEventMouseButton and e.pressed:
        if e.button_index == MOUSE_BUTTON_WHEEL_UP:
            dist = max(3.0, dist * 0.9)
        elif e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            dist = min(60.0, dist * 1.1)
    elif e is InputEventMouseMotion \
            and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
        azim -= e.relative.x * 0.005
        elev = clamp(elev + e.relative.y * 0.005, -1.4, 1.4)

func _process(_dt: float) -> void:
    var pos := ziel + dist * Vector3(
        cos(elev) * sin(azim), sin(elev), cos(elev) * cos(azim))
    look_at_from_position(pos, ziel, Vector3.UP)
