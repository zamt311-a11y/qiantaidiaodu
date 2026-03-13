def test_login_page_available(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert "账号登录" in res.text
