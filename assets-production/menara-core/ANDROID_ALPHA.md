# UTMKL REAL WORLD · 0.1.0 Alpha

Android 10+，目标 Android 16（API 36）。包名 `my.utmkl.realworld`，版本码 2，可覆盖同一签名的 Android Preview。应用没有随 APK 分发 JNI 库，Android WebView 由设备提供，安装包适用于 ARM64 和 x86_64。

下载 APK 到 Android 设备，在文件管理器打开。系统询问时允许该来源安装应用。使用支持 WebGL 2 的 Android System WebView。游戏、模型、Sky HDR、解码器和高斯测试样本随 APK 提供，启动使用 Capacitor 本地资源桥。

## 场景与操作

左摇杆控制移动，空白区域滑动控制视角。飞行模式可用上升、下降按钮，关闭飞行后返回地面。双指缩放，右上角截图保存到 `Pictures/UTMKL`。画质档位包括 Low、Medium、High、Ultra 和 Cinematic。首启读取 WebView、WebGL 2、GPU 和纹理尺寸，在软件渲染器和内存受限环境从 Low 启动。活动画面动态调节像素比。

塔楼和主场地优先解码，树木及 HDR 随后加载。36 张 GLB 材质纹理转为带 mipmap 的 KTX2/Basis UASTC，纹理由 WebView 根据 GPU 支持选择转码格式。塔楼和场地网格保留上一阶段结构。高斯模块按需加载，离开展区时释放样本。截图在设备允许时支持最高 3840×2160，受限 GPU 上限为 2560×1440。

「高斯测试」中的 122,490 个 Gaussian 来自 Necessity Robotics 的印度公园扫描。它是独立的 Spark 验证场景。Menara Razak 校园场景仍为模型和真实来源 PBR 材质。真实 UTMKL Gaussian 数据状态见原报告。 [样本与许可](https://necessityrobotics.github.io/explore.html?map=oak_160543) · [UTMKL 数据状态](UTMKL_GAUSSIAN_STATUS.md)

## 构建与证书

使用 Node.js 22+、JDK 21、Android SDK API 36、Build Tools 36.0.0 和 Gradle 8.14.3。Linux x86_64 构建机还需 Python 3 和 Pillow。运行 `npm ci` 后执行 `scripts/build-android.sh`。脚本使用仓库外的 `UTMKL_KEYSTORE` 与 `UTMKL_KEY_PASSWORD_FILE`，并在签名后对照旧 APK 的证书、公钥身份、Manifest 和 ZIP 对齐。既有证书的 SHA-256 为：

```
15cd110285f026084af2bb0a48ef519e90ae24b0b289208d730d8ca9586efc45
```

Web / Windows 离线包继续使用原始共享模型。Android 使用同一源场景和网格的压缩纹理变体。实现参考 Capacitor Android 桥和官方插件接口，截图通过 Android MediaStore 写入相册。 [Capacitor](https://github.com/ionic-team/capacitor) · [Capacitor Plugins](https://github.com/ionic-team/capacitor-plugins) · [Spark](https://github.com/sparkjsdev/spark) · [Three.js KTX2Loader](https://github.com/mrdoob/three.js/blob/dev/docs/pages/KTX2Loader.html)
