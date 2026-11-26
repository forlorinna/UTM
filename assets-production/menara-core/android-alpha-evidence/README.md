# Android Alpha 出包与 WebGL 证据

`mobile-web-*.png` 是从公开发布的签名 APK 提取 `assets/public` 后，在 Linux Chromium SwiftShader 中运行同一前端取得的截图。触控、双指缩放、跳跃、相机切换、飞行、五档切换与图片导出通过。独立样本验证 122,490 个 Gaussian 已在 Spark 渲染循环提交。浏览器测试使用本地校验夹具，手机 App 运行入口为 Capacitor 资源桥。

`APK_VERIFICATION.txt` 记录 Android SDK 核验结果，签名与上一版相同，目标 API 36。APK 包含共享模型、36 张 GPU 纹理、场地数据、编译前端和独立样本。 [公开 Release](https://github.com/forlorinna/UTM/releases/tag/utmkl-real-world-v0.1.0-alpha)
