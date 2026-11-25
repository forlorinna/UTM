# UTMKL Campus Life

非官方、离线的 UTM 吉隆坡校区样板，版本 0.1.0。独立 Godot 4.7.2 工程。

## 启动

Android 安装文件为 UTMKL-Campus-Life-0.1.0-arm64.apk。支持 ARM64，最低 Android 7.0（API 24），目标 Android 16（API 36）。使用本次构建的独立测试签名。Android 提示时，可对当前文件管理器允许安装该 APK。Android 会拒绝覆盖签名不同的同包名应用。

桌面打开 project.godot，等待 Godot 导入资源，再按 F5。游戏保存于 Godot 的 user://campus.cfg。设置提供 English、中文和 Bahasa Melayu。

| 操作 | 桌面 |
| --- | --- |
| 步行、跑步、跳跃 | WASD、Shift、Space |
| 第一/第三人称 | V |
| 飞行、升降、速度档位 | F、Space/Ctrl、G |
| 车辆上下车与刹车 | 走近白色轿车按 E，WASD 驾驶，Space 刹车 |
| 打开地图及设置 | M、Esc |
| 摄影模式 | C |
| 进入虚构阅览室 | 走进 Menara Razak 前广场按 R，或从设置前往 |

触屏左侧按住拖动可移动，右侧滑动看向。底栏提供视角、飞行、驾驶和阅览室按钮。设置中可控制天气、时钟、画质、语言、人物密度和校园活动。摄影模式隐藏人物和部分界面。驾驶 HUD 提示靠左行驶。

## 构建和复现

1. 使用 Godot 4.7.2 同版本 Android 导出模板、JDK 和 SDK Platform 36 / Build Tools 36。在 Godot 的 Editor Settings → Export → Android 中配置 SDK、JDK 和本地测试签名。
2. 设置 ANDROID_SDK_ROOT，执行 tools/build_android.sh 并传入 APK 输出路径。脚本导入、导出、验证签名、16 KB 页对齐、ZIP 结构、Manifest、ABI 和联网权限，并输出 SHA256。后续升级需保持签名和包名一致。
3. 用独立的 XDG_DATA_HOME 运行 godot --headless --path . --script res://tests/runtime.gd -- --test 。自动测试会写入并移除测试存档。
4. 地图由 tools/import_geography.py 重建，需要 pyproj、源 OSM XML 和公共 Skadi 高程瓦片。用 Blender 4.3.2 运行 tools/model_menara.py、tools/model_mjiit.py 与 tools/model_southeast.py。后两个脚本导入同目录几何工具，运行时把 tools 加到 Python 模块搜索路径。
5. tools/fetch_assets.py 可联网复查并下载 Poly Haven 原始文件，需要 curl 和 ImageMagick identify。源码已含可离线导入的游戏资产，以及可重建派生模型的树、车和人物动画原件。

文件索引见 docs/reference_index.md、docs/visual_audit.md、data/research/campus_buildings.csv 与 data/assets_manifest.json。

本版包含 Menara Razak、MJIIT、Residensi UTMKL、Masjid UTMKL 四座独立外观地标。其他轮廓可在小地图和建筑档案查看。校区尚未完成全量三维重建，阅览室使用虚构布局。Android 真机验证尚待进行。
