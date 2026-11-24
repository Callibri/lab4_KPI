import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from boxoffice.audit.contract import AuditService
from boxoffice.bootstrap import build_app

N, DELAY = 10, 0.2


class DownAudit(AuditService):
    def record(self, entry):
        raise ConnectionError("audit down")

    def list_entries(self, limit=50, offset=0, entity_type=None):
        return []


def run(mode, **kw):
    with tempfile.TemporaryDirectory() as d:
        app = build_app(f"sqlite:///{d}/b.db", mode=mode, **kw)
        c = TestClient(app)
        creds = {"email": "b@example.com", "password": "secret123"}
        c.post("/auth/register", json=creds)
        c.headers["Authorization"] = "Bearer " + c.post("/auth/login", json=creds).json()["access_token"]
        mid = c.post("/movies", json={"title": "M", "genre": "G", "release_date": "2024-01-01",
                                      "budget_usd": 100}).json()["id"]
        times, codes = [], []
        for i in range(N):
            t = time.perf_counter()
            r = c.post(f"/movies/{mid}/reports", json={"report_date": f"2024-02-{i + 1:02d}", "region": "US",
                                                      "revenue_usd": 10, "tickets_sold": 1})
            times.append((time.perf_counter() - t) * 1000)
            codes.append(r.status_code)
        t = time.perf_counter()
        app.state.bus.wait_idle(30)
        drain = (time.perf_counter() - t) * 1000
        audited = len(app.state.audit_service.list_entries(limit=200, entity_type="report"))
        return statistics.mean(times), drain, set(codes), audited, len(app.state.bus.dead_letters)


print(f"{N} POST /movies/{{id}}/reports; затримка аудиту = {DELAY * 1000:.0f} мс\n")
print(f"{'режим':<26}{'сер. відповідь, мс':>20}{'дочекатись обробки, мс':>24}{'коди':>8}{'записів аудиту':>16}")
for label, mode, kw in [
    ("без побічних операцій", "none", {}),
    ("sync  (аудит працює)", "sync", {"audit_delay_s": DELAY}),
    ("async (аудит працює)", "async", {"audit_delay_s": DELAY}),
    ("sync  (аудит ВПАВ)", "sync", {"audit_service": DownAudit()}),
    ("async (аудит ВПАВ)", "async", {"audit_service": DownAudit()}),
]:
    avg, drain, codes, audited, dead = run(mode, **kw)
    extra = f"  dead letters: {dead}" if dead else ""
    print(f"{label:<26}{avg:>20.1f}{drain:>24.1f}{str(sorted(codes)):>8}{audited:>16}{extra}")
