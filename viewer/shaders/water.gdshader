shader_type spatial;
render_mode blend_mix, depth_draw_always, cull_disabled;

uniform vec4 flach : source_color = vec4(0.25, 0.60, 0.78, 0.55);
uniform vec4 tief : source_color = vec4(0.04, 0.20, 0.34, 0.85);

void vertex() {
    VERTEX.y += 0.05 * sin(VERTEX.x * 1.3 + TIME * 1.6)
              + 0.04 * sin(VERTEX.z * 1.9 - TIME * 1.2);
}

void fragment() {
    ALBEDO = mix(flach.rgb, tief.rgb, 0.5);
    ALPHA = mix(flach.a, tief.a, 0.5);
    ROUGHNESS = 0.12;
    METALLIC = 0.25;
}
