# Menara Razak 单栋资产验收

## 本阶段文件

- `Menara_Razak.blend` 是 Blender 4.5.3 LTS 的可编辑源工程。图像已打包，保留分组、材质节点、米制坐标、相机与灯光。
- `Menara_Razak.glb` 是同一建筑的独立 glTF 2.0 资产。包含建筑及入口近场，使用内嵌贴图、玻璃透射与 IOR 扩展。Khronos 校验为 0 错误、0 警告。使用独立 Blender 进程重新导入后确认 11 张 4096×4096 内嵌贴图。
- `renders/01_SW_Curtain_Wall.png`、`02_NE_Stone_and_Crown.png`、`03_Entry_Canopy.png` 是三张 1920×1080 的 Cycles CPU 渲染。启用自适应采样和 OpenImageDenoise，最大 80 采样。
- `renders/04_Independent_Gaussian_India.png` 是独立高斯测试，不计入三张建筑渲染。数据地点为印度。
- `SHA256SUMS` 可校验模型和图像文件。

校内其他建筑、地图、UI、APK 和玩法暂停改动。本模型的路面范围限于入口台阶、门前硬铺及建筑边缘。

## 原工程审计

| 事项 | 证据 |
| --- | --- |
| 三维资产 | Real World 分支有 4 个 BLEND、31 个 GLB、1 个 SPZ、1 个 SPLAT，未找到已跟踪的 FBX 或 PLY。以 Blender 打开原 `art/Menara_Razak.blend` 成功，场景包含 13 个网格对象。 |
| Blender 调用 | 既有 Cycles 日志记录 6 张树木材质卡和 40 采样的 1920×1080 校园鸟瞰图。本阶段另安装经 SHA-256 核对的 Blender 4.5.3 LTS Linux x86_64，在 4 核 CPU 配额下使用 Cycles CPU 和 OIDN。 |
| 高斯渲染 | 既有截图中，Spark 实际渲染了 Marcel Padilla 的 113,648 高斯植物样本。本轮重新下载 Necessity Robotics 的户外 SPZ，复现 122,490 高斯裁切，用 Chromium / WebGL 2 / Spark 重新渲染并目视检查。 |
| 已实现并验证 | 原 Real World 的外景步行、视角、地点导航、天气、浏览器 4K 截图和高斯展区有实现与验证。原 APK 在 Android 11 软件模拟器完成安装，模拟器系统界面无响应，Android 图形启动和真机表现仍待验证。 |
| 仅写入需求或尚无可验收产物 | UTMKL 本地 3DGS / 摄影测量扫描、建筑 GIS 与扫描融合、全校照片级重建、手机上 8K 或渐进光追摄影。以上没有纳入本次成果。 |

## 建筑照片比对

| 构造 | 本阶段建模与实际修正 |
| --- | --- |
| 西南立面 | 由 OSM 平面轮廓定位弧面，分区建立蓝玻璃、浅色横带、窄竖柱和西段双层外挑遮阳片。玻璃单独建面，使用实体厚度、Low-E 色差、透射和隐藏式窗帘。 |
| 东北立面 | 依据背面真实照片加入通高红色端部、浅色实体墙、深框洞口、竖向玻璃带和凹陷条窗。第一轮试渲染中使用的绿色漆面更换为中性的真实混凝土扫描，露出屋冠之下的暗色百叶并修正取景裁切。 |
| 屋冠 | 连续曲面包含收尖的端部、外挑银色边缘、分段底面与直立锁边，屋冠文字和支架为几何。 |
| 入口 | 两张 UTM NewsHub 实拍确定圆白柱、分格弧形玻璃雨棚、暖色墙面、入口门楣、台阶及右侧凸出的带栏杆平台。补充了压条、点式玻璃固定件、门框、门把、栏杆及独立文字，并按成图检查修正底层空缺与右侧未分格玻璃。 |
| 实测边界 | OSM 给出的约 54 m 与 18 层是建模依据。各构件尺寸、背后室内结构、屋面曲率与被遮挡的部分由照片和轮廓估算。圆形徽记为简化几何。模型未经现场测量或扫描校准。 |

建筑参考照片只用于建模比对，未嵌入模型或公开上传。来源包括 [Khairul hazim 西南立面](https://commons.wikimedia.org/wiki/File:Menara_Razak_at_UTM_Kuala_Lumpur.JPG)、[CEphoto, Uwe Aranas 东北立面](https://commons.wikimedia.org/wiki/File:Kuala_Lumpur_Malaysia_UTM-Campus-Kuala-Lumpur-03a.jpg)、[UTM 招生简章的屋冠视角](https://razak.utm.my/wp-content/uploads/2020/09/MPhil_2020_UTMRazak.pdf)、[UTM NewsHub 2025 入口](https://news.utm.my/2025/05/kerjasama-strategik-utm-dan-mimos-perkasa-penggunaan-ai-dalam-kdn/) 与 [2022 入口](https://news.utm.my/2022/07/razak-faculty-of-technology-informatics-rfti-utm-silpakorn-university-su-thailand-summer-school-program/)。

轮廓数据来自 © OpenStreetMap contributors，按 ODbL 1.0 使用。4K PBR 扫描来自 Poly Haven CC0，使用了混凝土、金属、铺地的颜色、法线、粗糙度与金属度贴图，混凝土颜色图做了中性化处理。环境采用 2K HDRI 与独立日光。 [OSM 轮廓](https://www.openstreetmap.org/way/552610255) · [ODbL](https://www.openstreetmap.org/copyright) · [Poly Haven 许可](https://polyhaven.com/license) · [混凝土](https://polyhaven.com/a/concrete_wall_007) · [金属](https://polyhaven.com/a/metal_plate_02) · [入口石面](https://polyhaven.com/a/concrete_floor_02) · [砖铺地](https://polyhaven.com/a/brick_floor_003) · [HDRI](https://polyhaven.com/a/urban_street_04)

独立高斯验证使用 Shaded park walk，由 Necessity Robotics（xclean）采集并重建，CC BY 4.0。本次将发布的 Lite SPZ 按 20 m 半径裁切到 122,490 个高斯，保留原始变换、旋转和尺度。公开检索未确认可再分发的 UTMKL 高斯扫描。 [原始扫描与说明](https://necessityrobotics.github.io/explore.html?map=oak_160543) · [数据](https://huggingface.co/datasets/Pyassahu/xclean-maps/tree/main/maps_nrs/oak_160543) · [许可](https://creativecommons.org/licenses/by/4.0/)

## 复现

BLEND 已打包，可以直接打开并切换三个相机。标牌使用的 DejaVu 字体许可见 FONT_LICENSE.txt。若需重新生成，从 `source/` 下载 CC0 贴图后运行建模。Python 环境需要 requests、Pillow 与 NumPy，Blender 使用 4.5.3 LTS。

```sh
cd source
python fetch.py
python refine_material.py
blender -b -t 4 --python build_menara.py -- --output ../rebuild
blender -b ../rebuild/Menara_Razak.blend -t 4 --python render_menara.py
blender -b ../rebuild/Menara_Razak.blend --python export_menara.py -- ../rebuild/export
python package_glb.py ../rebuild/export ../rebuild/Menara_Razak.glb
```

GLB 导出时使用单独的三角化副本，保留正本的可编辑拓扑。4K 材质贴图保留原分辨率，GLB 内的粗糙度与金属度组合贴图使用高质量 JPEG 压缩。
