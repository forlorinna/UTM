# Android Alpha 出包与 WebGL 证据

`mobile-web-*.png` 是从公开发布的签名 APK 提取 `assets/public` 后，在 Linux Chromium SwiftShader 中运行同一前端取得的截图。触控、双指缩放、跳跃、相机切换、飞行、五档切换与图片导出通过。独立样本验证 122,490 个 Gaussian 已在 Spark 渲染循环提交。浏览器测试使用本地校验夹具，手机 App 运行入口为 Capacitor 资源桥。

`APK_VERIFICATION.txt` 记录 Android SDK 核验结果，签名与上一版相同，目标 API 36。APK 包含共享模型、36 张 GPU 纹理、场地数据、编译前端和独立样本。 [公开 Release](https://github.com/forlorinna/UTM/releases/tag/utmkl-real-world-v0.1.0-alpha)

## Android 16 原生测试

使用 Android 16 / API 36 的 x86_64 软件模拟器。设备无 KVM，启动期间系统看门狗终止过 `system_server`。调整测试模拟器的超时后，系统报告 `sys.boot_completed=1`，签名 APK 已完整传入设备。ADB 流式安装与本地 Package Manager 安装均未返回成功。最后一次本地安装在 95 秒后超时，未进入原生活动。覆盖升级仅通过旧版证书和版本码比对验证。ARM64 实机与骁龙 / Adreno 性能仍待实测。
