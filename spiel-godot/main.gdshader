shader_type canvas_item;

uniform float fog_strength : hint_range(0.0, 2.0) = 1.2;
uniform vec3 fog_color = vec3(0.0, 0.0, 0.0); // чёрный туман

void fragment() {
    float h = UV.y;                     // 0 сверху, 1 снизу
    float pulsate = 0.5 + 0.5 * sin(TIME * 0.3);
    float alpha = fog_strength * (0.5 + 0.5 * h) * pulsate;

    // Ограничим максимум, чтобы не уходило в 100% чёрный
    alpha = clamp(alpha, 0.0, 0.85);

    COLOR = vec4(fog_color, alpha);
}
