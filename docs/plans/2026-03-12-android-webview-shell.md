# Android 原生壳 + WebView 复用地图 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为外场工程师提供 Android 客户端（Kotlin 原生壳 + WebView），复用现有后端地图页面完成“登录/地图任务/工参图层/任务详情”等核心能力，并为后续“拍照上传/离线/推送”预留扩展点。

**Architecture:** Android 仅负责权限、定位/拍照等系统能力与 WebView 容器；业务 UI 与地图渲染复用后端模板页（新增移动端专用页面），通过 token 注入与 WebView<->JS 桥实现融合。

**Tech Stack:** Android (Kotlin + AndroidX + Material)；WebView；后端 FastAPI 模板页（复用 [map.html](file:///e:/python/%E7%BD%91%E4%BC%98%E5%A4%96%E5%9C%BA%E6%99%BA%E8%81%94%E4%BD%9C%E4%B8%9A%E8%B0%83%E5%BA%A6%20APP/backend/app/templates/map.html) 的 JS 逻辑并做移动端适配）；REST API（现有 `/api/*`）。

---

## 0. 现状与约束

- 后端已经提供：
  - 登录与 token：`POST /api/auth/login`，并在前端通过 `localStorage.token` 存储（见 [map.html](file:///e:/python/%E7%BD%91%E4%BC%98%E5%A4%96%E5%9C%BA%E6%99%BA%E8%81%94%E4%BD%9C%E4%B8%9A%E8%B0%83%E5%BA%A6%20APP/backend/app/templates/map.html#L39-L73)）。
  - 地图任务/工参渲染：高德 JS API + 任务/扇区接口。
- Android 端采用 WebView 复用地图：
  - WebView 需要显式开启地理定位与文件选择能力，否则 “定位/上传照片” 会不可用。
  - WebView 的 `navigator.geolocation` 权限需要通过 `WebChromeClient.onGeolocationPermissionsShowPrompt` 授权。

---

## Task 1：创建 Android 工程骨架（android/）

**Files:**
- Create: `android/settings.gradle.kts`
- Create: `android/build.gradle.kts`
- Create: `android/app/build.gradle.kts`
- Create: `android/app/src/main/AndroidManifest.xml`
- Create: `android/app/src/main/java/com/netopt/app/MainActivity.kt`
- Create: `android/app/src/main/res/layout/activity_main.xml`
- Create: `android/app/src/main/res/xml/network_security_config.xml`

**Step 1: 写入最小可运行的 WebView 容器**

`activity_main.xml`（只包含 WebView）：

```xml
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
  android:layout_width="match_parent"
  android:layout_height="match_parent">

  <WebView
    android:id="@+id/webview"
    android:layout_width="match_parent"
    android:layout_height="match_parent" />

</FrameLayout>
```

`MainActivity.kt`（加载后端移动端入口 URL）：

```kotlin
package com.netopt.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.webkit.GeolocationPermissions
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
  private lateinit var webView: WebView

  private val requestLocation = registerForActivityResult(
    ActivityResultContracts.RequestPermission()
  ) { granted ->
    if (granted) webView.reload()
  }

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_main)

    webView = findViewById(R.id.webview)
    webView.webViewClient = WebViewClient()
    webView.webChromeClient = object : WebChromeClient() {
      override fun onGeolocationPermissionsShowPrompt(
        origin: String,
        callback: GeolocationPermissions.Callback
      ) {
        callback.invoke(origin, true, false)
      }
    }

    val s = webView.settings
    s.javaScriptEnabled = true
    s.domStorageEnabled = true
    s.cacheMode = WebSettings.LOAD_DEFAULT
    s.setGeolocationEnabled(true)
    s.mediaPlaybackRequiresUserGesture = false

    ensureLocationPermission()
    webView.loadUrl(BuildConfig.BASE_URL + "/m/map")
  }

  private fun ensureLocationPermission() {
    val p = Manifest.permission.ACCESS_FINE_LOCATION
    val ok = ContextCompat.checkSelfPermission(this, p) == PackageManager.PERMISSION_GRANTED
    if (!ok) requestLocation.launch(p)
  }
}
```

**Step 2: Manifest 权限与网络配置**

`AndroidManifest.xml`（核心权限 + 明确 usesCleartextTraffic 用于局域网 http 调试）：

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <uses-permission android:name="android.permission.INTERNET" />
  <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />

  <application
    android:usesCleartextTraffic="true"
    android:networkSecurityConfig="@xml/network_security_config"
    android:label="网优外场智联作业调度">
    <activity android:name=".MainActivity" android:exported="true">
      <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
      </intent-filter>
    </activity>
  </application>
</manifest>
```

`network_security_config.xml`（允许局域网/开发态 http）：

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
  <base-config cleartextTrafficPermitted="true" />
</network-security-config>
```

**Step 3: 本地开发可配置后端地址**

在 `android/app/build.gradle.kts` 增加 BuildConfig 字段：

```kotlin
android {
  defaultConfig {
    buildConfigField("String", "BASE_URL", "\"http://10.0.2.2:8000\"")
  }
}
```

**Step 4: 验证**

- 目标：Android 工程能跑起来并打开 WebView，显示移动端地图页 `/m/map`。
- 手工验证：
  - 后端启动后，在模拟器中打开 App，应出现地图页面（若高德 key 未配置会提示）。

---

## Task 2：后端新增移动端地图入口（/m/map）

**Files:**
- Modify: `backend/app/admin/routes.py`
- Create: `backend/app/templates/mobile_map.html`

**Step 1: 新增路由**

在 `backend/app/admin/routes.py` 添加：

```python
@router.get("/m/map", response_class=HTMLResponse)
def mobile_map(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "mobile_map.html",
        {
            "request": request,
            "amap_key": settings.amap_web_key,
            "amap_security_js_code": settings.amap_security_js_code,
        },
    )
```

**Step 2: 复用 map.html 的业务逻辑并做移动端布局适配**

`mobile_map.html` 目标：
- 保留核心 JS（任务/扇区加载、筛选、关联任务等）。
- 将左侧 380px 面板改为移动端顶部/抽屉布局：
  - 默认展示地图全屏；
  - 一个“筛选/图层”按钮打开面板；
  - 面板内复用现有筛选控件。

建议实现方式：
- 直接复制 [map.html](file:///e:/python/%E7%BD%91%E4%BC%98%E5%A4%96%E5%9C%BA%E6%99%BA%E8%81%94%E4%BD%9C%E4%B8%9A%E8%B0%83%E5%BA%A6%20APP/backend/app/templates/map.html) 到 `mobile_map.html`；
- 修改 CSS：
  - `#wrap` 改为单列；
  - `#panel` 改为 `position: fixed` 抽屉；
  - 增加一个“打开面板”按钮与遮罩层；
- JS 不改动业务逻辑，仅加打开/关闭抽屉方法。

**Step 3: 验证**

运行后端，浏览器访问 `/m/map`：
- 能加载地图；
- 登录后可看到任务点、扇区图层；
- “附近任务/筛选/搜索弹窗/查看关联任务”可用。

---

## Task 3：在 WebView 中支持 token 注入（可选增强，减少重复登录）

**Files:**
- Modify: `android/app/src/main/java/com/netopt/app/MainActivity.kt`

**Step 1: 定义 token 存储**

使用 `SharedPreferences` 保存登录 token（先不做加密，后续再接 AES/Keystore）。

**Step 2: WebView 注入 localStorage**

当本地已存 token 时，在 `onPageFinished` 执行：

```kotlin
webView.evaluateJavascript("localStorage.setItem('token', '$token');") { }
```

然后 `reload()` 一次，让页面以登录态加载。

**Step 3: 验证**
- 第一次打开：通过页面登录；
- 关闭 App 再打开：应自动保持登录态。

---

## Task 4：定位能力联动（WebView geolocation + 地图中心/附近任务）

**Files:**
- Modify: `android/app/src/main/java/com/netopt/app/MainActivity.kt`
- Modify: `backend/app/templates/mobile_map.html`

**Step 1: WebView geolocation 授权**
- 确保 `setGeolocationEnabled(true)` 已开启；
- 处理 runtime 权限拒绝场景：页面提示“请在系统设置开启定位权限”。

**Step 2: 移动端体验：增加“定位到我”按钮**
- 在 `mobile_map.html` 增加一个浮动按钮：
  - 点击后通过 `navigator.geolocation.getCurrentPosition` 获取坐标；
  - 调用高德 JS `map.setCenter([lng, lat])`；
  - 可选：自动勾选“附近任务”并刷新。

**Step 3: 验证**
- 模拟器/真机开启定位后，点击“定位到我”能把地图中心拉到当前位置；
- 打开“附近任务”能看到以中心点过滤后的任务。

---

## Task 5：文件选择与照片上传（为异常反馈铺路）

**Files:**
- Modify: `android/app/src/main/java/com/netopt/app/MainActivity.kt`
- Modify: `backend/app/templates/mobile_map.html`（或后续新增 `mobile_tasks.html`）
- Verify: `backend/app/api/routes/tasks.py` 是否已有 `POST /api/tasks/{id}/photos`

**Step 1: WebView file chooser**
- 实现 `WebChromeClient.onShowFileChooser`；
- 使用 `ActivityResultContracts.StartActivityForResult` 返回 Uri；
- 允许相机拍照与相册选择（后续再做）。

**Step 2: 后端上传接口对齐**
- 若 `POST /api/tasks/{id}/photos` 缺失或不满足 1-3 张限制，补齐校验并写测试。

**Step 3: 验证**
- 在 Web 页面选择文件能成功上传并在任务详情中可回显（回显 UI 可后续做）。

---

## Task 6：工程师端任务首页（后续，建议 Web 先落地）

**Files:**
- Create: `backend/app/templates/mobile_home.html`
- Modify: `backend/app/admin/routes.py`（新增 `/m/home`）

**目标：**
- 首页 4 个入口：我的待执行 / 今日 / 明日 / 异常；
- 点列表项进入任务详情（可复用现有弹窗模板或独立页面）。

---

## Backlog（对照需求文档未完善项）

对照 [网优外场智联作业调度 APP工具需求分析.md](file:///e:/python/%E7%BD%91%E4%BC%98%E5%A4%96%E5%9C%BA%E6%99%BA%E8%81%94%E4%BD%9C%E4%B8%9A%E8%B0%83%E5%BA%A6%20APP/%E7%BD%91%E4%BC%98%E5%A4%96%E5%9C%BA%E6%99%BA%E8%81%94%E4%BD%9C%E4%B8%9A%E8%B0%83%E5%BA%A6%20APP%E5%B7%A5%E5%85%B7%E9%9C%80%E6%B1%82%E5%88%86%E6%9E%90.md)：
- 智能路线规划、次日安排清单：未实现
- 撤回派发/调度调整规则：部分缺失
- 消息通知：未实现
- 数据统计与报表导出：未实现
- 离线缓存：未实现
- 操作日志与加密存储：未实现

