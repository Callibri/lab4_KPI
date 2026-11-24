import time

import pytest
from fastapi.testclient import TestClient

from boxoffice.audit.contract import AuditEntry, AuditService
from boxoffice.bootstrap import build_app

MOVIE = {"title": "Dune", "genre": "Sci-Fi", "release_date": "2024-03-01", "budget_usd": 1000}
REPORT = {"report_date": "2024-03-05", "region": "US", "revenue_usd": 500, "tickets_sold": 50}


def make_client(tmp_path, mode, **kw):
    app = build_app(f"sqlite:///{tmp_path / 'db.sqlite'}", mode=mode, **kw)
    client = TestClient(app)
    creds = {"email": "t@example.com", "password": "secret123"}
    client.post("/auth/register", json=creds)
    token = client.post("/auth/login", json=creds).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return app, client


def settle(app):
    assert app.state.bus.wait_idle(5)


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_business_actions_are_audited_in_both_modes(tmp_path, mode):
    app, client = make_client(tmp_path, mode)
    mid = client.post("/movies", json=MOVIE).json()["id"]
    client.post(f"/movies/{mid}/reports", json=REPORT)
    settle(app)
    actions = [e["action"] for e in client.get("/audit").json()]
    assert actions == ["user.registered", "movie.created", "report.added"]
    assert client.get("/audit", params={"entity_type": "report"}).json()[0]["details"]["revenue_usd"] == 500


def test_sync_response_time_includes_audit_but_async_does_not(tmp_path):
    delay = 0.3
    (tmp_path / "s").mkdir()
    (tmp_path / "a").mkdir()
    _, sync_client = make_client(tmp_path / "s", "sync", audit_delay_s=delay)
    _, async_client = make_client(tmp_path / "a", "async", audit_delay_s=delay)

    t = time.perf_counter()
    sync_client.post("/movies", json=MOVIE)
    sync_time = time.perf_counter() - t
    t = time.perf_counter()
    async_client.post("/movies", json=MOVIE)
    async_time = time.perf_counter() - t

    assert sync_time >= delay
    assert async_time < delay


class BrokenAudit(AuditService):
    def record(self, entry: AuditEntry) -> bool:
        raise ConnectionError("audit service unavailable")

    def list_entries(self, limit=50, offset=0, entity_type=None):
        return []


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_audit_outage_does_not_break_main_operation(tmp_path, mode):
    app, client = make_client(tmp_path, mode, audit_service=BrokenAudit())
    resp = client.post("/movies", json=MOVIE)
    assert resp.status_code == 201
    settle(app)
    assert client.get(f"/movies/{resp.json()['id']}").status_code == 200


def test_async_outage_ends_in_dead_letters_after_retries(tmp_path):
    app, client = make_client(tmp_path, "async", audit_service=BrokenAudit())
    client.post("/movies", json=MOVIE)
    settle(app)
    assert len(app.state.bus.dead_letters) >= 1


def test_redelivered_event_does_not_create_duplicate_audit_records(tmp_path):
    app, client = make_client(tmp_path, "async")
    client.post("/movies", json=MOVIE)
    settle(app)
    bus = app.state.bus
    from boxoffice.application.events import MovieCreated
    from datetime import date
    event = MovieCreated(movie_id=99, title="X", genre="g", release_date=date(2024, 1, 1), budget_usd=1)
    bus.publish(event)
    bus.publish(event)
    settle(app)
    ids = [e["entity_id"] for e in client.get("/audit", params={"entity_type": "movie"}).json()]
    assert ids.count(99) == 1
