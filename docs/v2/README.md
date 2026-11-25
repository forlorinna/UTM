# UTMKL Reality Engine 2.0.0-preview.1

这是独立分支上的 Godot 4 安卓预览版。0.1.0 的源码版本固定在 `1f420b21ca47b8b004bc23bf5d8487d70f8494a4`。新增模型的 Blender 工程在 `art/v2`，Godot 使用的 GLB、碰撞、扫描图和 HDRI 在 `assets/runtime`。

## 建筑复建

| 对象 | 已导入 | 证据及局限 |
| --- | --- | --- |
| Menara Razak | 独立曲面主体、分段幕墙和遮阳、酒红垂直带、弧面屋盖和机电构件、开放入口台阶 | 17 层主体加估算的技术层。结构尺度来自 OSM 轮廓，近入口、背立面和屋顶无实测。公开照片证据见 [Commons](https://commons.wikimedia.org/wiki/File:Menara_Razak_at_UTM_Kuala_Lumpur.JPG)、[Bernama](https://www.bernama.com/en/news.php?id=2345956) 和 [校园形态论文](https://www.planningmalaysia.org/index.php/pmj/article/download/1693/1372/2581)。 |
| MJIIT | 独立庭院轮廓、中央 X 支撑、多层弧形裙楼、窗台和雨棚 | 入口按照片建模，背部开窗与屋顶未测量。[外观照片](https://www.myras.org/blog/our-blog-1/mjiit-advanced-robotic-lab-55) · [官方导览](https://utmspace.viewin360.co/share/collection/7K4yZ) |
| Residensi UTM | 七层裙楼与四栋不同的住宅塔楼，包括阳台、侧墙和屋面设备 | 航拍有四塔证据，楼高、各塔层数和连廊关系存在近似。[UTM 航拍](https://news.utm.my/2017/05/utm-student-residential-complex-offers-complete-self-contained-accommodation/) · [官方导览](https://utmspace.viewin360.co/share/collection/7K4yc) |
| 校园主入口 | 独立上折屋盖、柱跨、固定门侧服务空间、入口高差和照明 | 照片有正向特征。绝对高程、屋后布置、植被位置仍近似。[Bernama 照片](https://www.bernama.com/en/news.php?id=2345956) |
| 其他 68 个 OSM 建筑轮廓 | 其中 Masjid 保留旧版，67 个只有地图登记 | [逐栋状态表](../../data/research/campus_buildings.csv)。整个校园未达到逐栋验收。 |

新建筑各有三个 LOD 和独立碰撞。入口、幕墙、屋顶等实际进入游戏。道路和停车沿已登记几何，应用扫描沥青、补丁、路缘、排水格栅。地面采用两个实拍扫描的不同尺度和正常的粗糙度、法线混合。现有地形原始高程间隔约 31 米。公共阅览室沿用原作虚构布局。三栋地标的外部和入口完成本阶段重建，真实室内重建仍待完成。玻璃采用分格粗糙度和天空反射，近景仍缺真实内部视差和逐面校核。

参考入口和校园拓扑已主动检索 [UTM 官方校图与导览](https://kl.utm.my/project/campus-map-virtual-tour/) 与 [UTMSPACE 全景入口](https://utmspace.edu.my/utmspace-homepage/campus-virtual-tour/)。已查看可获取的导览封面和实照。官方地图 PDF 直接访问未得到有效 PDF。建筑名、地形和道路的测绘依据见 [前版资料索引](../reference_index.md)。仅将允许再分发的来源用于游戏资产。

## 资源数量

| 类别 | 已下载并保存来源及散列 | 最终目标 |
| --- | ---: | ---: |
| PBR 扫描材质 | 22 | 200 |
| HDRI | 12 | 12 |
| 街景道具 | 8 | 150 |
| 植物模型 | 12 | 40 |
| 独立建筑细部资产库 | 尚未建立逐项验收计数 | 100 |

材质库存包含 Poly Haven 20 套与 ambientCG 2 套。HDRI 有 5 套运行时探针。新街景道具有 2 个导入，其中花槽在场景中布置。新植物模型有 9 个导入，其中 7 个在场景中布置。植物采购数是独立模型条目，部分树木或地被为相邻形态参考，未确认校区实地物种。旧游戏的道具与植物未用于冲抵采购指标。建筑脚本生成了多个专用构件，未将重复实例折算为独立细部库。

来源和许可证见 [原始下载清单](../../data/v2/acquired_assets.json)、[植物来源](../../data/v2/innerscene_assets.json)、[运行纹理清单](../../data/v2/runtime_textures.json)。资产来源为 [Poly Haven](https://polyhaven.com/license)、[ambientCG](https://docs.ambientcg.com/license/) 与 [Innerscene](https://www.innerscene.com/royalty-free-3d-models)。依照来源页面及清单记录使用。非明确授权的建筑照片用作建模参考，未放入 APK。

## 复现

使用 Godot 4.7.2、Blender 4.3.2、JDK 21 和 Android SDK Build Tools 36。项目原有的步行、车辆、飞行、时间、天气、读书室及存档流程沿用。运行检查和构建入口如下。

```bash
godot --headless --editor --import --quit
godot --headless --script res://tests/runtime.gd -- --test
godot --headless --script res://tools/audit_runtime.gd -- --test --audit /tmp/utmkl-audit
tools/build_android.sh /tmp/UTMKL-Campus-Life-V2-preview-arm64.apk
```

重建单个地标可运行 `blender -b -t 4 --python tools/rebuild_menara_razak.py`，其余入口见同目录。桌面 Compatibility 软件渲染与真机性能是两项独立验收。此预览版仍需要真机 FPS、安装、热稳定性与实景验收。

本地 APK 与原本地 0.1.0 使用同一个调试证书。GitHub CI 使用当次构建的临时测试证书。设备存在同包名且证书不同的旧安装时，Android 要求卸载旧版再安装，卸载会清除该应用本地存档。
