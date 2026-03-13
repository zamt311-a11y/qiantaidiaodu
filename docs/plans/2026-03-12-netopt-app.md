# 网优外场智联作业调度 APP 全量开发实施计划

> **Goal:** 用最低成本（单机部署、无对象存储/无Redis）实现：任务导入与管理、地图任务可视化、4G/5G工参扇区可视化、调度派发、进度更新、照片上传、消息通知、统计报表。  
> **默认选型（可调整）:** 后端 FastAPI + MySQL；管理端 Web（FastAPI 模板页 + 高德 JS API）；Android App（Kotlin + 高德 Android SDK）。  
> **部署目标:** 1 台服务器（MySQL + 后端 + 本地文件目录），文件保存在服务器本地目录。

---

## 0. 目录与边界

### 0.1 仓库结构（建议）
- `backend/`：FastAPI 后端（REST API + 管理端页面）
- `android/`：Android 客户端（Kotlin）
- `data/`：本地文件目录（工参/照片/备份），生产环境映射到服务器目录
- `docs/`：需求、计划、接口说明

### 0.2 MVP 交付闭环（优先跑通）
1. 账号登录（管理员/工程师）
2. 管理员导入任务 Excel/CSV → 任务列表 & 地图任务点
3. 管理员导入 4G/5G 工参 CSV → 生成扇区 GeoJSON → 地图图层展示
4. 管理员派发任务给工程师 → 工程师端看到“我的任务/今日/明日”
5. 工程师更新任务状态 + 提交异常 + 上传照片

### 0.3 非 MVP（后续增强）
- 智能路线规划（先用简单最近邻/分区策略占位）
- 离线缓存（Android Room + 同步队列）
- AES-256 数据加密（先做配置预留，后续逐字段上线）
- 推送（极光）与站内消息联动
- 统计图表与报表导出细化

---

## 1. 数据模型（第一版）

### 1.1 用户与权限
- `users`：手机号、姓名、角色（admin/engineer）、密码哈希、启用状态
- 登录：先用手机号+密码；短信验证码作为后续增强

### 1.2 任务
- `tasks`：站点ID、站点名称、经纬度、任务类型、优先级、计划时间、状态、负责人、地址、备注
- `task_events`：状态变更、异常提交、操作人、时间（审计）
- `task_photos`：照片文件路径、关联任务、上传人、时间

### 1.3 工参与扇区
- `sectors`：制式（4G/5G）、CELLID、经纬度、方位角、频段/频点、原始字段（JSON）
- 扇区图形：后端计算 60° 扇形多边形，输出 GeoJSON

### 1.4 消息
- `messages`：收件人、类型、内容、已读状态、关联任务/扇区

---

## 2. API（第一版）

### 2.1 认证
- `POST /api/auth/login`
- `GET /api/me`

### 2.2 任务
- `POST /api/tasks/import`（CSV/Excel）
- `GET /api/tasks`（筛选：类型/状态/优先级/日期/负责人/附近半径）
- `GET /api/tasks/{id}`
- `PATCH /api/tasks/{id}`（状态、备注、异常）
- `POST /api/tasks/{id}/photos`
- `POST /api/tasks/dispatch`（管理员派发）

### 2.3 工参/扇区
- `POST /api/sectors/import`（4G/5G CSV）
- `GET /api/sectors`（筛选：制式/频段）
- `GET /api/sectors/geojson`（返回 GeoJSON FeatureCollection）
- `GET /api/sectors/{id}`
- `GET /api/sectors/{id}/tasks`（关联任务）

### 2.4 管理端页面
- `GET /admin/map`：地图页面（任务点+扇区图层+筛选）

---

## 3. 开发任务拆解（按先后顺序）

### Task A：后端骨架与配置
**Files（示例）**
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/*`
- Create: `backend/pyproject.toml` 或 `backend/requirements.txt`

**Steps**
1. 初始化 FastAPI 应用、配置读取（环境变量/`.env`）
2. 配置本地文件目录（工参/照片/备份），并校验可写
3. 引入数据库连接（先支持 SQLite 开发态，生产用 MySQL）

### Task B：数据模型与迁移
1. 定义 SQLAlchemy 模型（users/tasks/sectors/...）
2. 配 Alembic 迁移
3. 初始化管理员账号（命令或首次启动）

### Task C：任务导入与任务 API
1. 导入 CSV/Excel（字段校验、错误回传）
2. 任务列表筛选 & 附近任务（基于经纬度距离计算）
3. 状态流转与审计事件

### Task D：工参导入与扇区生成
1. 导入 4G/5G CSV（字段模糊匹配）
2. 频段推导（按频点/SSB 频点映射表）
3. 扇区多边形计算 → GeoJSON 输出

### Task E：管理端地图页
1. 用高德 JS API 渲染任务点
2. 叠加扇区 GeoJSON 图层，支持制式/频段开关与记忆
3. 点击任务点/扇区弹窗详情

### Task F：Android 客户端（后续轮次）
1. 登录、获取任务列表、地图任务点
2. 图层控制、扇区叠加、详情页
3. 任务状态更新、异常提交、照片上传
4. 离线缓存与同步（增强）

---

## 4. 验证策略（每个任务都要可验证）
- 后端：`pytest` + FastAPI TestClient（至少覆盖：登录、导入、GeoJSON 输出）
- 手工验证：启动后访问 `/admin/map`，能看到任务点与扇区图层

