def test_landing_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200


def test_sobre_page_loads(client):
    response = client.get("/sobre/")
    assert response.status_code == 200


def test_register_page_loads(client):
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_login_page_loads(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
