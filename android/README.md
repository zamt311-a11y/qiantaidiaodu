# Android WebView 壳工程

## 作用

用于外场工程师 Android 端：原生 Kotlin 壳 + WebView，默认加载后端页面 `/m/home`（任务列表/详情/更新/上传），并可从页面跳转到 `/m/map`（复用现有地图与工参逻辑）。

## 打开方式

- 用 Android Studio 打开 `android/` 目录
- 修改后端地址：`android/app/build.gradle.kts` 里的 `BuildConfig.BASE_URL`
  - 模拟器默认：`http://10.0.2.2:8000`
  - 真机同网段：`http://<你的服务器IP>:8000`

## 运行前置

- 后端需要能访问：`/m/map`（由后端提供）
- 后端需要能访问：`/m/home`（由后端提供）
- 若使用 HTTP（非 HTTPS），当前 Manifest 已允许明文流量（用于局域网调试）
- 真机定位需要在系统里授予定位权限

