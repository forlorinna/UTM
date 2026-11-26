# Build verification

The development build rendered through Chromium with SwiftShader WebGL 2. A scripted test traversed the landscape title screen, keyboard and pointer movement, first/third-person camera switching, footprint collision, landmark navigation, weather, graphics presets and the photo export flow. The in-app FPS counter reflects this software renderer during those checks and is not a hardware benchmark.

The gallery displayed Marcel Padilla’s original 113,648-splat Houseplant. It also displayed a crop of Shaded park walk containing 122,490 Gaussians after Spark’s initial GPU-backed sort. A local SPLAT file was imported and displayed. Both built-in exhibits were inspected visually.

The Blender offline still was rendered from the adapted campus mesh with Cycles at 1920 × 1080 and 40 samples. Its source scene was assembled from the runtime mesh and exported to glTF. It has a fixed camera.

The APK build checks the signing certificate, package manifest and ZIP alignment. This preview uses a dedicated stage signing key and a separate package identifier. Physical Android hardware performance is unmeasured.
