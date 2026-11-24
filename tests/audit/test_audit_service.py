from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import sessionmaker

from boxoffice.audit.contract import AuditEntry
from boxoffice.audit.service import SqlAuditService
from boxoffice.audit.storage import AuditBase
from boxoffice.infrastructure.db import make_engine


@pytest.fixture()
def audit(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'a.db'}")
    AuditBase.metadata.create_all(engine)
    return SqlAuditService(sessionmaker(bind=engine, expire_on_commit=False))


def entry(event_id="e1", entity_type="movie", entity_id=1):
    return AuditEntry(event_id, "movie.created", entity_type, entity_id,
                      datetime.now(timezone.utc), {"title": "Dune"})


def test_record_and_list(audit):
    assert audit.record(entry()) is True
    items = audit.list_entries()
    assert len(items) == 1 and items[0].details == {"title": "Dune"}


def test_duplicate_delivery_is_idempotent(audit):
    assert audit.record(entry("same")) is True
    assert audit.record(entry("same")) is False
    assert len(audit.list_entries()) == 1


def test_filter_and_pagination(audit):
    audit.record(entry("a", "movie", 1))
    audit.record(entry("b", "report", 2))
    assert [e.entity_type for e in audit.list_entries(entity_type="report")] == ["report"]
    assert len(audit.list_entries(limit=1, offset=1)) == 1
