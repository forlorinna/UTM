# UTMKL REAL WORLD for Android

This independent pre-release is a GIS-based explorable model of Universiti Teknologi Malaysia's Kuala Lumpur campus. It runs offline in Android System WebView using WebGL 2. The campus map uses OpenStreetMap data. Menara Razak, MJIIT, Masjid UTMKL and Residensi UTMKL reuse the dedicated reference models from UTMKL Campus Life.

## Play

- Install the signed APK on Android 10 or later with a current Android System WebView. The APK uses its own package ID, `my.utmkl.realworld`.
- Pull the left joystick to move. Drag the scene to turn. The lower-right controls switch view, fly, run or jump. The top-right map opens the landmark list.
- Set light and weather in Settings. Photo mode captures 1080p, 1440p or 4K JPEGs. Android saves them to Pictures/UTMKL. The Cycles button opens the packaged offline view.
- Open Gaussian gallery from the map. You can view the plant scan, switch to an outdoor scan recorded in India, or open a local PLY, SPLAT, SPZ or KSPLAT. The external scans are independent exhibits.

## Build

Use Node 20+, a full JDK 17 or 21, Python 3, Android SDK Platform 35 and Build Tools 35.0.0. Set `ANDROID_SDK_ROOT` to the SDK installation.

```sh
cd game
npm ci
npm run build
cd ../android
./build.sh
```

The build script places the verified APK in `android/product/`. It generates a local stage key when none exists. Locally generated keys cannot update an APK installed with a different key. Keep private keystores out of source control.

The spatial data, texture maps, cropped SPZ, landmarks, character and offline render are packaged. See `game/public/THIRD-PARTY-NOTICES.txt`.

## Source procedures

- Regenerate `game/public/campus.json` with `game/scripts/geography.py`, the OSM extract listed in the notices and Python packages Pillow and Shapely. The script fetches public elevation tiles and caches them beside the XML.
- `game/scripts/crop_spz.py` creates the mobile crop from the published outdoor SPZ, trajectory and keyframes.
- Launch `npm run dev -- --port 4173` from `game/`. `node qa/check.mjs` executes the WebGL browser checks using system Chromium. `node qa/export.mjs` exports glTF for `game/scripts/cycles_still.py`. Blender Cycles generates a fixed-camera JPEG independently of live WebGL. Set the last argument to the desired sample count.
- `game/scripts/tree_cards.py` renders tree impostors from the Poly Haven tree models.

## Reconstruction limits

LiDAR or phone scans of UTMKL were unavailable from the verified public sources. The campus mixes surveyed map outlines with approximate elevation, modeled exterior detail and representative streetscape elements. Vehicle models are scenery. The accessible campus consists of exterior exploration. Gaussian Splatting is available in the independent gallery.
