# UTM Kuala Lumpur 参考资料

检索日期 2026-11-25。制作范围为吉隆坡 Jalan Sultan Yahya Petra / Jalan Maktab 校区。Kolej Siswa Jaya 是校外住宿，未纳入建模范围。公开照片和导览封面用于外观比对。可分发的纹理来自许可证见清单的资产库。

## 官方地图、导览和设施

| 资料 | 获取情况和用途 |
| --- | --- |
| [UTM KL Map & Virtual Tour](https://kl.utm.my/project/campus-map-virtual-tour/) | 搜索索引显示校图和导览，直接网页请求返回 502。 |
| [UTMSPACE 360° 导览](https://utmspace.edu.my/utmspace-homepage/campus-virtual-tour/) | 已读取 KL 分区链接，实际下载并查看五处官方导览的公开封面。尚未逐场景核对互动全景。 |
| [UTM 学生事务校图 PDF](https://studentaffairs.utm.my/wp-content/uploads/sites/29/2020/06/Peta-UTMKL.pdf) | 通过网页索引读取分区与建筑代码。直接下载返回 HTML，具体建筑身份仍需结合现状逐栋核对。 |
| [UTMKL Services & Facilities](https://kl.utm.my/services-facilities/) | 索引确认公开停车、图书馆、校车相关设施。 |
| [Facilities Gallery](https://kl.utm.my/facilities-gallery/) · [公开场地预订](https://dvcdev.utm.my/kl/space-rental/) | 核对 Dewan Azman Hashim、Dewan Tan Sri Ainuddin Wahid 和 Read Cafe。 |
| [Visitor](https://kl.utm.my/visitor/) · [Getting Around](https://kl.utm.my/getting-around/) | 官方校址、47.56 英亩的历史介绍、公共交通。地图边界使用 OSM 校界。 |
| [Campus Life](https://kl.utm.my/campus-life/) · [MJIIT Facilities](https://mjiit.utm.my/chee/facilities/) | 核对校外住宿、公开学习设施和 MJIIT 用途。 |
| [UTM Library branches](https://library.utm.my/branches/) | 校区图书馆与 Menara Razak 内的 Read Cafe 分开登记。独立阅览室关卡明确采用虚构布局。 |

## 建筑证据

| 建筑 | 资料与局限 |
| --- | --- |
| Menara Razak | [Khairul hazim 拍摄的南向立面](https://commons.wikimedia.org/wiki/File:Menara_Razak_at_UTM_Kuala_Lumpur.JPG) 与 [官方 360° 入口预览](https://utmspace.viewin360.co/share/collection/7KNp5)。弧形屋盖、幕墙分带和入口参考照片。OSM 标记 18 层、54 米。侧背面细部和入口高程有近似。 |
| MJIIT | [正立面照片](https://www.myras.org/blog/our-blog-1/mjiit-advanced-robotic-lab-55) 与 [官方导览](https://utmspace.viewin360.co/share/collection/7K4yZ)。米黄色裙座、蓝白楼层、中央 X 支撑及多层雨棚有照片依据。高度、背面分格和屋顶后部为近似。 |
| Residensi UTMKL | [UTM NewsHub 航拍与四塔资料](https://news.utm.my/2017/05/utm-student-residential-complex-offers-complete-self-contained-accommodation/) 与 [官方 360° 裙楼预览](https://utmspace.viewin360.co/share/collection/7K4yc)。按七层裙楼和 11–22 层塔楼的文献范围建模，个别塔位、准确层数和屋顶细部为近似。 |
| Masjid UTMKL | [官方 360° 入口预览](https://utmspace.viewin360.co/share/collection/7KN5Q) 与上列 UTM NewsHub 航拍。金色穹顶、蓝色层叠屋面和两处宣礼塔为照片可见特征。高度、确切方向与局部入口构件有待核对。 |
| Dewan Azman Hashim | [官方导览](https://utmspace.viewin360.co/share/collection/7KNNd) 的入口封面已核对。尚未将场馆与唯一 OSM 轮廓对应。 |
| 其他建筑 | OSM 中已登记的轮廓、名称与已知层数见 campus_buildings.csv。需核对其他实楼、屋顶及未映射附属建筑。 |

## 地理与许可

- OSM 校界为 way 1076507073。原始请求是 [OSM API bbox](https://api.openstreetmap.org/api/0.6/map?bbox=101.7162,3.1699,101.7230,3.1762)。离线工程包附带原始几何、要素 ID 及派生地图。快照移除了编辑账号字段。数据库适用 [ODbL 1.0](https://www.openstreetmap.org/copyright)。
- 坐标使用 EPSG:32647。原点为经度 101.719524、纬度 3.172784。Godot X 为网格东，Z 为网格南，Y 向上。1 单位为 1 米。Y 零点为地形数据高程 50 米。
- 地形来自 [Mapzen Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) 的公开 [N03E101 Skadi 瓦片](https://s3.amazonaws.com/elevation-tiles-prod/skadi/N03/N03E101.hgt.gz)。该纬度原始分辨率约 31 米，游戏以 5 米采样和 80 米分块生成地形和碰撞。局部阶差和建筑基座高程需要现场核验。参见 [Terrain Tiles attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)。
- 渲染采用 Godot 4 Mobile/Vulkan 与桌面 Compatibility，包含 HDRI 天空和反射、方向光与局部灯光。参见 [Godot 渲染器说明](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)。
