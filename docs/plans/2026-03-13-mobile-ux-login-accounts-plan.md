# Mobile UX + Login + 账号管理 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add unified login with role-based redirect, improve account management permissions, fix CSV encoding issues, and enhance mobile map UX.

**Architecture:** Extend role checks to include `super_admin`, add a global `/login` page with front-end redirects, centralize CSV decoding (auto + manual encoding), and refine `/m/map` UX behaviors in `map.html`.

**Tech Stack:** FastAPI, Jinja2 templates, SQLAlchemy, vanilla JS.

---

### Task 1: Extend Roles & Account Management APIs

**Files:**
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/db/init_db.py`
- Modify: `backend/app/schemas/user.py`
- Modify: `backend/app/api/routes/users.py`
- Test: `backend/tests/test_user_admin_roles.py`

**Step 1: Write the failing test**

```python
def test_admin_cannot_create_admin(client, admin_token):
    resp = client.post("/api/users", json={"phone":"1","name":"n","role":"admin","password":"p"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 403
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_user_admin_roles.py::test_admin_cannot_create_admin -v`  
Expected: FAIL (route allows admin to create admin today).

**Step 3: Write minimal implementation**

```python
def require_admin(current_user):
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(...)
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_user_admin_roles.py::test_admin_cannot_create_admin -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/deps.py backend/app/db/init_db.py backend/app/schemas/user.py backend/app/api/routes/users.py backend/tests/test_user_admin_roles.py
git commit -m "feat: add super admin role rules for user management"
```

---

### Task 2: Unified Login Page + Role Redirect

**Files:**
- Create: `backend/app/templates/login.html`
- Modify: `backend/app/admin/routes.py`
- Modify: `backend/app/mobile/routes.py`
- Modify: `backend/app/templates/map.html`
- Modify: `backend/app/templates/tasks.html`
- Modify: `backend/app/templates/import.html`
- Modify: `backend/app/templates/sectors.html`
- Modify: `backend/app/templates/report.html`
- Modify: `backend/app/templates/mobile_home.html`
- Test: `backend/tests/test_login_page.py`

**Step 1: Write the failing test**

```python
def test_login_page_available(client):
    resp = client.get("/login")
    assert resp.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_login_page.py::test_login_page_available -v`  
Expected: FAIL (route missing).

**Step 3: Write minimal implementation**

```python
@router.get("/login")
def login_page(request: Request): ...
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_login_page.py::test_login_page_available -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/templates/login.html backend/app/admin/routes.py backend/app/mobile/routes.py backend/tests/test_login_page.py backend/app/templates/*.html
git commit -m "feat: add unified login page and role redirect"
```

---

### Task 3: CSV Encoding Auto + Manual Select

**Files:**
- Modify: `backend/app/api/routes/tasks.py`
- Modify: `backend/app/api/routes/sectors.py`
- Modify: `backend/app/templates/import.html`
- Test: `backend/tests/test_imports.py`

**Step 1: Write the failing test**

```python
def test_import_tasks_gbk_csv(client, admin_token):
    content = "站点ID,经度,纬度\nA,1,2\n".encode("gbk")
    resp = client.post("/api/tasks/import", files={"file": ("t.csv", content, "text/csv")}, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_imports.py::test_import_tasks_gbk_csv -v`  
Expected: FAIL (decode error or乱码).

**Step 3: Write minimal implementation**

```python
def decode_csv_bytes(data, encoding=None):
    # try utf-8-sig, utf-8, gb18030, gbk, gb2312, utf-16
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_imports.py::test_import_tasks_gbk_csv -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/routes/tasks.py backend/app/api/routes/sectors.py backend/app/templates/import.html backend/tests/test_imports.py
git commit -m "feat: add csv encoding detection and manual select"
```

---

### Task 4: Mobile Map UX Improvements

**Files:**
- Modify: `backend/app/templates/map.html`
- Modify: `backend/app/templates/tasks.html`
- Optional Test: `backend/tests/test_mobile_ui_markers.py`

**Step 1: Write the failing test**

```python
def test_mobile_map_contains_route_toggle(client):
    resp = client.get("/m/map")
    assert "routeToggle" in resp.text
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_mobile_ui_markers.py::test_mobile_map_contains_route_toggle -v`  
Expected: FAIL

**Step 3: Write minimal implementation**

```html
<div id="routeToggle">显示规划路线</div>
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_mobile_ui_markers.py::test_mobile_map_contains_route_toggle -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/templates/map.html backend/app/templates/tasks.html backend/tests/test_mobile_ui_markers.py
git commit -m "feat: improve mobile map ux"
```

