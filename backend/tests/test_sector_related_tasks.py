from fastapi.testclient import TestClient


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_sector_related_tasks_filters_by_sector_shape_and_permissions(client: TestClient, admin_token: str) -> None:
    from app.core.security import hash_password
    from app.db.session import SessionLocal
    from app.models.sector import Sector
    from app.models.task import Task
    from app.models.user import User

    with SessionLocal() as db:
        engineer = User(
            phone="13900000000",
            name="工程师A",
            role="engineer",
            password_hash=hash_password("pw123"),
            is_active=True,
        )
        db.add(engineer)
        db.commit()
        db.refresh(engineer)

        sector = Sector(
            network="4G",
            cell_id="C1",
            lon=0.0,
            lat=0.0,
            azimuth_deg=0.0,
            band="1",
            freq="100",
            raw_fields_json="{}",
        )
        db.add(sector)
        db.commit()
        db.refresh(sector)

        t_inside_admin = Task(
            site_id="S_in_admin",
            site_name="站点-扇区内-admin",
            lon=0.0,
            lat=0.004,
            task_type="单验",
            priority="中",
            status="待执行",
            address="A",
            remark="",
            assignee_id=None,
        )
        t_inside_engineer = Task(
            site_id="S_in_eng",
            site_name="站点-扇区内-eng",
            lon=0.0,
            lat=0.003,
            task_type="单验",
            priority="中",
            status="待执行",
            address="B",
            remark="",
            assignee_id=engineer.id,
        )
        t_outside = Task(
            site_id="S_out",
            site_name="站点-扇区外",
            lon=0.004,
            lat=0.0,
            task_type="单验",
            priority="中",
            status="待执行",
            address="C",
            remark="",
            assignee_id=engineer.id,
        )
        db.add_all([t_inside_admin, t_inside_engineer, t_outside])
        db.commit()
        db.refresh(t_inside_admin)
        db.refresh(t_inside_engineer)
        db.refresh(t_outside)

        sector_id = sector.id
        inside_admin_id = t_inside_admin.id
        inside_engineer_id = t_inside_engineer.id
        outside_id = t_outside.id

    res = client.get(
        f"/api/sectors/{sector_id}/related_tasks?radius_m=1000",
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 200
    ids = {t["id"] for t in res.json()}
    assert inside_admin_id in ids
    assert inside_engineer_id in ids
    assert outside_id not in ids

    login = client.post("/api/auth/login", json={"phone": "13900000000", "password": "pw123"})
    assert login.status_code == 200
    eng_token = login.json()["access_token"]

    res2 = client.get(
        f"/api/sectors/{sector_id}/related_tasks?radius_m=1000",
        headers=_auth_headers(eng_token),
    )
    assert res2.status_code == 200
    ids2 = {t["id"] for t in res2.json()}
    assert inside_engineer_id in ids2
    assert inside_admin_id not in ids2
    assert outside_id not in ids2

