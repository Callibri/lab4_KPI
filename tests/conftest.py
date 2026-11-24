import pytest
from fastapi.testclient import TestClient

from boxoffice.bootstrap import build_app


@pytest.fixture()
def app():
    return build_app("sqlite://", mode="none")


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def auth_client(client):
    creds = {"email": "tester@example.com", "password": "secret123"}
    assert client.post("/auth/register", json=creds).status_code == 201
    token = client.post("/auth/login", json=creds).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
