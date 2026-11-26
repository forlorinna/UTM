#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

: "${ANDROID_HOME:?Set ANDROID_HOME to an SDK with platform and build tools 36}"
: "${UTMKL_KEYSTORE:?Set the path to the protected release keystore}"
: "${UTMKL_KEY_PASSWORD_FILE:?Set the path to the restricted keystore password file}"
asset_python=${UTMKL_ASSET_PYTHON:-python3}
gradle=${UTMKL_GRADLE:-"$PWD/android/gradlew"}
sdk="$ANDROID_HOME/build-tools/36.0.0"
out=${UTMKL_ANDROID_OUTPUT:-"$PWD/android/app/build/verified"}
mkdir -p "$out"
apk="$out/UTMKL_REAL_WORLD_v0.1.0_Alpha.apk"
unsigned="$PWD/android/app/build/outputs/apk/release/app-release-unsigned.apk"

"$asset_python" scripts/prepare-mobile-assets.py
npm run build
rm "dist/assets/Core_Site.glb" "dist/assets/Core_Tree.glb" "dist/assets/Menara_Razak_Runtime.glb"
npx cap sync android
"$gradle" -p android :app:assembleRelease "$@"
"$sdk/apksigner" sign --ks "$UTMKL_KEYSTORE" --ks-pass "file:$UTMKL_KEY_PASSWORD_FILE" \
  --ks-key-alias utmkl-stage --v2-signing-enabled true --v3-signing-enabled true \
  --out "$apk" "$unsigned"
legacy="$PWD/../../android-real-world/releases/UTMKL-Real-World-0.1.0.apk"
fingerprint() { "$sdk/apksigner" verify --print-certs "$1" | awk '/certificate SHA-256 digest:/{print $NF}'; }
test "$(fingerprint "$apk")" = "$(fingerprint "$legacy")"
"$sdk/apksigner" verify --verbose --print-certs "$apk"
"$sdk/zipalign" -c -P 16 4 "$apk"
"$sdk/aapt2" dump badging "$apk"
unzip -tq "$apk"
(cd "$out" && sha256sum "${apk##*/}" > SHA256SUMS)
