# Menara Razak 核心区步行样板

场景以 Menara Razak 为中心。步行覆盖约 127 × 83 m 的 OSM 局部裁切，包含入口、四级台阶、平台、砖铺区、两段服务路与环形车道、步道、路缘、树木、座凳和灯具。相邻建筑轮廓只用于保留地块和阻挡越界。校内建筑资产仅有 Menara Razak。

## 运行

解压 `Menara_Core_Walk_Web.zip`。Windows 有 Python 3 时双击 `START_WINDOWS.cmd`，其他系统运行 `python3 serve.py`。入口为 `http://127.0.0.1:4270/`。资源都在压缩包内，运行时无需联网，需支持 WebGL 2 的浏览器。

WASD 或方向键移动，拖动视角，点击场景可锁定鼠标。R 返回入口，P 或截图按钮保存去掉界面的 PNG。原地站立与构图均为第一人称。入口门作为外景边界处理。

| 画质 | 阴影图 | 渲染像素比上限 | 截图目标 |
| --- | --- | --- | --- |
| High | 1024 | 1.0 | 1920×1080 |
| Ultra | 1536 | 1.45 | 2560×1440 |
| Cinematic | 2048 | 2.0 | 3840×2160 |

设备纹理尺寸可能限制截图分辨率。三个档位共用建筑几何，屏幕像素比随显示器上限调整。幕墙在 High 使用不透明反射，在 Ultra 使用部分透射，在 Cinematic 使用完整透射。已在 Linux Chromium 的 WebGL 2 软件后端测试，未测量各设备帧率。

## 交付文件

- `Menara_Core.blend` 是带贴图的 Blender 4.5.3 核心区工程，包括六个相机、地形、设施、夜间灯、雨水和近场树木。
- `public/assets/Core_Site.glb` 是运行场地，`Menara_Razak_Runtime.glb` 是上一阶段建筑的运行材质版本。几何沿用上一阶段模型，贴图最长边压缩到 1536 像素。浏览器隐藏旧展台小件，场地和设施由 Core_Site 提供。实时和离线共用外景地面几何与树木源资产。
- `renders/` 保存六张 1920×1080 原始 PNG。白天正面、白天斜侧、入口、屋冠特写、黄昏、雨后。
- `evidence/` 保存实际步行画面、顶阶停靠、截图按钮生成的 PNG，以及构建、模型校验、在线程有限的 CPU 上完成的渲染记录和自动测试记录。
- `MENARA_RAZAK_QA.md` 与 `UTMKL_GAUSSIAN_STATUS.md` 保存参考比对、未测量项与高斯数据状态。

## 几何与来源

道路中心线及环形车道来自原项目的 OSM 数据。路宽、绿化和灯具按照片与可通行关系重建。地形基于同一 DEM 数据，入口近场做了局部找平。没有标定过的线宽、人行道排布、座凳、灯具和树木坐标均为估算。斑马线用于样板通行布局，未有现场记录。雨后图的积水位置是表现配置。 [OSM 署名与许可](https://www.openstreetmap.org/copyright) · [UTM 校园图](https://studentppsm.utmspace.edu.my/wp-content/uploads/2024/08/Peta-UTM-KL.pdf) · [UTM 入口实拍](https://news.utm.my/2025/05/kerjasama-strategik-utm-dan-mimos-perkasa-penggunaan-ai-dalam-kdn/)

使用 Poly Haven 的 Leafy Grass、Asphalt Track、Island Tree 02、Street Lamp 01 等 CC0 资产；草地漫反射做了颜色修正。建筑、砖和石面继承上一阶段的许可记录。 [Poly Haven 许可](https://polyhaven.com/license) · [草地材质](https://polyhaven.com/a/leafy_grass) · [沥青](https://polyhaven.com/a/asphalt_track) · [树木](https://polyhaven.com/a/island_tree_02) · [路灯](https://polyhaven.com/a/street_lamp_01) · [塔楼来源](../menara-razak/README.md)

## 复现

浏览器源代码与资产位于同一目录。运行 `npm ci && npm run build && npm test`。产物目录为 `dist/`。运行 `npm run preview -- --port 4287` 后可用 Chromium 执行 `node qa/browser.mjs`。

离线镜头与光照由 `source/render_core.py` 配置。从已打包的工程渲染全部图像可运行 `blender -b Menara_Core.blend -t 4 --python source/render_core.py -- ./renders`。`source/site_data.py` 从仓库的 `data/map.json` 重建局部配置；`source/build_core.py` 从上阶段 BLEND 和本轮草地贴图生成场地；`source/runtime_glb.py` 打包运行贴图。`source/repair_tree_glb.py` 修复原项目树模型中的退化切线。完整命令见源脚本入口与参数。
