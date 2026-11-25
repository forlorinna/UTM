shader_type spatial;
render_mode diffuse_burley;

uniform sampler2D turf_color : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D turf_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D turf_roughness : filter_linear_mipmap, repeat_enable;
uniform sampler2D broad_color : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D broad_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D broad_roughness : filter_linear_mipmap, repeat_enable;
varying vec2 ground_position;
uniform float wetness : hint_range(0,1) = 0.0;

void vertex() {
	ground_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xz;
}

void fragment() {
	vec2 fine_uv = ground_position / 3.7;
	vec2 broad_uv = mat2(vec2(0.910,0.415), vec2(-0.415,0.910)) * ground_position / 15.0;
	vec3 fine = texture(turf_color, fine_uv).rgb;
	vec3 broad = texture(broad_color, broad_uv).rgb;
	// The transition follows the broad photographic scan, with no generated noise.
	float coverage = smoothstep(0.10, 0.32, broad.g) * 0.59;
	ALBEDO = mix(fine * vec3(0.43,0.65,0.67), broad * vec3(0.45,0.69,0.65), coverage) * (1.0 - wetness * 0.17);
	NORMAL_MAP = mix(texture(turf_normal, fine_uv).rgb, texture(broad_normal, broad_uv).rgb, coverage * 0.52);
	NORMAL_MAP_DEPTH = 0.42;
	ROUGHNESS = clamp(mix(texture(turf_roughness, fine_uv).r, texture(broad_roughness, broad_uv).r, coverage) - wetness * 0.12, 0.48, 1.0);
	SPECULAR = 0.24 + wetness * 0.09;
}
