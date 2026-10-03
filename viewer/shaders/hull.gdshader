shader_type spatial;

// Eintauch-Darstellung: Farbe nach WELT-Y (Wasserlinie y=0).
uniform vec4 dry : source_color = vec4(0.85, 0.72, 0.50, 1.0);
uniform vec4 wet : source_color = vec4(0.42, 0.32, 0.22, 1.0);
uniform vec4 linie : source_color = vec4(0.0, 0.85, 1.0, 1.0);

void fragment() {
    vec3 wpos = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
    vec3 col = mix(wet.rgb, dry.rgb, step(0.0, wpos.y));
    float band = 1.0 - smoothstep(0.03, 0.10, abs(wpos.y));
    col = mix(col, linie.rgb, band * 0.85);
    ALBEDO = col;
    ROUGHNESS = 0.55;
}
