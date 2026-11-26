# Menara Razak 二次质量审查

## 证据与方法

并排查看了上一阶段三张正式图和三组真实照片。下表按可识别构造核查。照片视点、焦距和遮挡各不相同，无法用未经标定的像素距离换算实测尺寸。OSM 的 54 m、18 层和外轮廓用于约束模型；校园形态研究写作 17 层。资料的计层口径未厘清，本轮保留旧模型，并标记两个层数来源。 [旧阶段正式图](https://github.com/forlorinna/UTM/tree/d0c8f17b4aa645a2d1c8220d3db11b1183e7a864/assets-production/menara-razak/renders) · [OSM 552610255](https://www.openstreetmap.org/way/552610255) · [校园形态研究](https://www.planningmalaysia.org/index.php/pmj/article/download/1693/1372/2581)

| 旧图与参考 | 准确部分 | 估算部分 | 仍不准确部分 | 下一步修正方案 |
| --- | --- | --- | --- | --- |
| 01 西南幕墙对照 Khairul hazim 实拍 | 长而浅的塔楼轮廓、蓝玻璃、浅色横带、近中段白色竖构件。红色端部与屋顶铭牌出现在同一端 | 约 54 m 总高、层间距与被树遮住的低层分格。模型正面主段窗格名义宽约 1.1–1.4 m | 实拍左段更暗，中心白带更厚、节奏变化更明显；模型竖框分布较均匀，红色面从该视角露出偏多。照片遮挡右端，无法验证整个宽高投影 | 复测完整正立面，标定相机后用可见中层横带锚点逐层修齐；按区记录窗格数和横带上下缘 |
| 02 东北立面与屋冠对照 CEphoto 03a | 浅色实体墙、错落条窗、左段深窗格、右端通高红色面和屋顶暗带 | 红端宽度、屋面高差、外挑深度和窄端背后体量 | 实拍近端金属屋檐鼻部更圆，露出的蓝玻璃回折面更明显；模型近端轮廓偏直，窗洞序列过于规则 | 在能看到窄端的两个点位拍摄带长边约束的照片；按端部轮廓重做屋檐样条，并验证背后玻璃体量 |
| 03 入口对照 UTM 2022/2025 照片 | 白圆柱、分格玻璃雨棚、浅暖墙面、入口文字、台阶、右侧带栏杆平台的前后关系 | 雨棚出挑、柱间距、门洞、每级踏步和平台进深用照片相对比例估算 | 实拍雨棚前沿和水平分格弧更显著，玻璃更深，右侧平台的遮挡关系也更复杂；旧图金属面斑驳偏重，门洞偏宽 | 现场量柱中心距、门净宽和阶高；补摄仰角与侧角，重新校准雨棚弧线与遮挡关系 |

旧模型的底层标高差为 4.65 m，上一层 3.10 m，上部主要按 2.85 m 排布。门组标称总宽 5.79 m，雨棚建模宽约 13.1 m、最大出挑约 8.68 m，两根圆柱中心相距 8.95 m。塔冠沿长边的模型拱升约 1.0 m，东北向看到的红色主面宽约 15.35 m。这些数字来自上一阶段建模参数，用于后续实测校准。 [塔楼几何源文件](../menara-razak/source/build_menara.py)

参考图用于核查，没有打包进场景。 [西南照片](https://commons.wikimedia.org/wiki/File:Menara_Razak_at_UTM_Kuala_Lumpur.JPG) · [东北照片](https://commons.wikimedia.org/wiki/File:Kuala_Lumpur_Malaysia_UTM-Campus-Kuala-Lumpur-03a.jpg) · [UTM 2025 入口](https://news.utm.my/2025/05/kerjasama-strategik-utm-dan-mimos-perkasa-penggunaan-ai-dalam-kdn/) · [UTM 2022 入口](https://news.utm.my/2022/07/razak-faculty-of-technology-informatics-rfti-utm-silpakorn-university-su-thailand-summer-school-program/)

## 本轮复核后的范围

本轮保留已交付的塔楼几何，以免把未测量的照片差异硬编码成真实建筑尺寸。去掉旧场景展台，使用 OSM 裁切车道和入口平台，处理台阶上下的地面连续性。校内供步行核查的范围见现场配置，路宽、路缘、铺装、道具位置及 DEM 局部找平是重建参数。 [UTM 校园地图与导览](https://kl.utm.my/project/campus-map-virtual-tour/) · [UTM 校园图 PDF](https://studentppsm.utmspace.edu.my/wp-content/uploads/2024/08/Peta-UTM-KL.pdf)
