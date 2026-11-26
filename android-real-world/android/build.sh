#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
sdk="${ANDROID_SDK_ROOT:-$PWD/sdk}"
compiler="$sdk/build-tools/35.0.0"
platform="$sdk/platforms/android-35/android.jar"
product="$PWD/product"
mkdir -p "$product"/{obj,dex,assets}
rm -rf -- "$product/assets/world"
mkdir -p "$product/assets/world"
rm -f "$product"/{resources.zip,linked.apk,unsigned.apk,aligned.apk,UTMKL-Real-World-0.1.0.apk}
cp -a ../game/dist/. "$product/assets/world/"
"$compiler/aapt2" compile --dir app/res -o "$product/resources.zip"
"$compiler/aapt2" link -I "$platform" --manifest app/AndroidManifest.xml \
    -A "$product/assets" -o "$product/linked.apk" "$product/resources.zip"
javac --release 8 -cp "$platform" -d "$product/obj" app/java/my/utmkl/realworld/CampusActivity.java
"$compiler/d8" --release --min-api 29 --lib "$platform" --output "$product/dex" \
    $(find "$product/obj" -name '*.class' -print)
python - "$product" <<'PY'
import pathlib, shutil, sys, zipfile
dir = pathlib.Path(sys.argv[1])
out = dir / 'unsigned.apk'
shutil.copyfile(dir / 'linked.apk', out)
with zipfile.ZipFile(out, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(dir / 'dex/classes.dex', 'classes.dex')
PY
"$compiler/zipalign" -f 4 "$product/unsigned.apk" "$product/aligned.apk"
if [[ ! -e utmkl-stage.p12 ]]; then
  keytool -genkeypair -keystore utmkl-stage.p12 -storetype PKCS12 -storepass staginglocal \
    -alias utmkl-stage -keyalg RSA -keysize 3072 -validity 3650 -dname 'CN=UTMKL Stage Build'
fi
"$compiler/apksigner" sign --v2-signing-enabled true --v3-signing-enabled true --v4-signing-enabled false --ks utmkl-stage.p12 --ks-pass pass:staginglocal --out "$product/UTMKL-Real-World-0.1.0.apk" "$product/aligned.apk"
"$compiler/apksigner" verify --verbose --print-certs "$product/UTMKL-Real-World-0.1.0.apk"
"$compiler/zipalign" -c 4 "$product/UTMKL-Real-World-0.1.0.apk"
"$compiler/aapt" dump badging "$product/UTMKL-Real-World-0.1.0.apk" | head -12
