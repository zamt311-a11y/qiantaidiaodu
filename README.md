# 网优外场智联作业调度 APP

本仓库当前包含：
- `backend/`：FastAPI 后端（API + 管理端地图页面）
- `docs/`：需求与实施计划

## 后端启动（开发机）

1. 进入目录

```powershell
cd "E:\python\网优外场智联作业调度 APP\backend"
```

2. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

3. 配置环境变量
- 复制 `backend/.env.example` 为 `backend/.env`
- 填写：
  - `SECRET_KEY`
  - `AMAP_WEB_KEY`（高德 Web JS Key，用于 `/admin/map`）
  - `AMAP_SECURITY_JS_CODE`（可选：高德 JS 安全密钥 / securityJsCode）
  - `BOOTSTRAP_ADMIN_PHONE/BOOTSTRAP_ADMIN_PASSWORD`（首次启动自动创建管理员）

4. 启动

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

访问：
- 健康检查：`GET http://127.0.0.1:8000/health`
- 管理端地图：`http://127.0.0.1:8000/admin/map`
- 导入配置页：`http://127.0.0.1:8000/admin/import`

## 数据导入（管理端用接口）

- 任务导入：`POST /api/tasks/import`（CSV 或 xlsx）
- 工参导入：`POST /api/sectors/import`（CSV）

导入后打开 `/admin/map`，登录后点击“刷新”即可看到任务点与扇区图层。

## 任务导入模板

- CSV 模板文件：`docs/templates/tasks_template.csv`
- XLSX 模板文件：`docs/templates/任务.xlsx`

## 基础验证（开发机）

```powershell
cd "E:\python\网优外场智联作业调度 APP\backend"
pytest -q
```

