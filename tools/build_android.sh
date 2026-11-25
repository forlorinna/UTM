#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
apk_target="${1:-$project_root/out/UTMKL-Campus-Life.apk}"
apk_parent="$(dirname -- "$apk_target")"
mkdir -p "$apk_parent"
apk_target="$(cd -- "$apk_parent" && pwd)/$(basename -- "$apk_target")"
godot_bin="${GODOT_BIN:-godot}"
android_sdk="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
android_tools="${ANDROID_BUILD_TOOLS:-}"
if [[ -z "$android_tools" && -n "$android_sdk" ]]; then
    android_tools="$(find "$android_sdk/build-tools" -maxdepth 1 -mindepth 1 -type d | sort -V | tail -n 1)"
fi
if [[ -z "$android_tools" || ! -x "$android_tools/apksigner" || ! -x "$android_tools/aapt2" ]]; then
    echo "Set ANDROID_SDK_ROOT or ANDROID_BUILD_TOOLS to the installed Android SDK Build Tools." >&2
    exit 1
fi
log_base="${BUILD_LOG_DIR:-$(dirname -- "$apk_target")}"
mkdir -p "$log_base"
staged_dir="$(mktemp -d "$(dirname -- "$apk_target")/.apk-build.XXXXXX")"
trap 'rm -rf "$staged_dir"' EXIT
"$godot_bin" --headless --path "$project_root" --editor --import --quit > "$log_base/import-final.log" 2>&1
if rg -q 'Parse Error:|SCRIPT ERROR|^ERROR:.*(import|load.*res://)' "$log_base/import-final.log"; then
    echo "Godot import errors. See $log_base/import-final.log" >&2
    exit 1
fi
"$godot_bin" --headless --path "$project_root" --export-debug Android "$staged_dir/game.apk" > "$log_base/export.log" 2>&1
"$android_tools/apksigner" verify --verbose --print-certs "$staged_dir/game.apk" > "$log_base/apk-signature.log"
"$android_tools/aapt2" dump badging "$staged_dir/game.apk" > "$log_base/apk-manifest.log" 2>&1
"$android_tools/aapt2" dump xmltree --file AndroidManifest.xml "$staged_dir/game.apk" > "$log_base/apk-xml-manifest.log" 2>&1
"$android_tools/zipalign" -c -P 16 4 "$staged_dir/game.apk" > "$log_base/apk-alignment.log"
unzip -tq "$staged_dir/game.apk" > "$log_base/apk-zip.log"
rg -q "package: name='com.forlorinna.utmklcampuslife'" "$log_base/apk-manifest.log"
rg -q "native-code: 'arm64-v8a'$" "$log_base/apk-manifest.log"
if rg -q 'android.permission.INTERNET' "$log_base/apk-xml-manifest.log"; then
    echo "Unexpected internet permission in the offline APK." >&2
    exit 1
fi
mv -f -- "$staged_dir/game.apk" "$apk_target"
(cd -- "$(dirname -- "$apk_target")" && sha256sum "$(basename -- "$apk_target")") > "$apk_target.sha256"
ls -lh "$apk_target"
cat "$apk_target.sha256"
