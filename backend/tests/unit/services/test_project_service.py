"""Unit tests for ProjectService."""

from datetime import datetime
import pytest

from backend.src.services.project_service import ProjectService
from backend.src.utils.errors import ValidationError, PartialSyncError


class DummyConnection:
    def __init__(self, server_url: str, organization=None):
        self.server_url = server_url
        self.organization = organization


class DummyProject:
    def __init__(self, pid: int, key: str, name: str):
        self.id = pid
        self.project_key = key
        self.name = name
        self.description = None
        self.last_analysis_date = None


class FakeConnectionRepo:
    def __init__(self, connection):
        self.connection = connection

    def get_by_id(self, _connection_id):
        return self.connection


class FakeProjectRepo:
    def __init__(self):
        self.by_key = {}
        self.created = []
        self.updated = []
        self.projects = []
        self.total = 0

    def get_by_key(self, connection_id, project_key):
        return self.by_key.get((connection_id, project_key))

    def create(self, **kwargs):
        self.created.append(kwargs)

    def update(self, project):
        self.updated.append(project)

    def list_by_connection(self, connection_id, page, page_size):
        return self.projects, self.total

    def get_by_id(self, project_id):
        return DummyProject(project_id, f"k-{project_id}", "proj")


class FakeMetricsRepo:
    def __init__(self):
        self.latest = {}
        self.branches = {}

    def get_latest_snapshot(self, project_id):
        return self.latest.get(project_id)

    def get_branches(self, project_id):
        return self.branches.get(project_id, [])


class FakeClient:
    def __init__(self, _url, _token):
        self.closed = False

    def get_projects(self, organization=None):
        return []

    def close(self):
        self.closed = True


@pytest.fixture
def service(monkeypatch):
    svc = ProjectService(db=None)
    svc.connection_repo = FakeConnectionRepo(DummyConnection("https://sonarqube.local"))
    svc.project_repo = FakeProjectRepo()
    svc.metrics_repo = FakeMetricsRepo()
    monkeypatch.setattr("backend.src.services.project_service.SonarQubeClient", FakeClient)
    return svc


def test_sync_projects_requires_org_for_sonarcloud(service):
    service.connection_repo = FakeConnectionRepo(DummyConnection("https://sonarcloud.io", organization=None))

    with pytest.raises(ValidationError):
        service.sync_projects_from_sonarqube(connection_id=1, token="tkn")


def test_sync_projects_raises_partial_sync_when_too_many_failures(service, monkeypatch):
    class ClientManyFailures(FakeClient):
        def get_projects(self, organization=None):
            return [
                {"project_key": "ok1", "name": "Project 1"},
                {"project_key": "bad-no-name"},
                {"name": "No key"},
            ]

    monkeypatch.setattr("backend.src.services.project_service.SonarQubeClient", ClientManyFailures)

    with pytest.raises(PartialSyncError) as exc:
        service.sync_projects_from_sonarqube(connection_id=1, token="tkn")

    assert exc.value.total_projects == 3
    assert len(exc.value.failed_projects) == 2


def test_sync_projects_creates_updates_and_skips_invalid(service, monkeypatch):
    existing = DummyProject(10, "existing_key", "Old Name")
    service.project_repo.by_key[(1, "existing_key")] = existing

    class ClientMixed(FakeClient):
        def get_projects(self, organization=None):
            return [
                {"project_key": "existing_key", "name": "New Name", "description": "upd"},
                {"project_key": "new_key", "name": "Brand New", "description": "new"},
                {"project_key": "invalid_only_key"},
            ]

    monkeypatch.setattr("backend.src.services.project_service.SonarQubeClient", ClientMixed)

    result = service.sync_projects_from_sonarqube(connection_id=1, token="tkn")

    assert result["synced_count"] == 2
    assert result["new_count"] == 1
    assert result["updated_count"] == 1
    assert result["failed_count"] == 1

    assert existing.name == "New Name"
    assert len(service.project_repo.updated) == 1
    assert len(service.project_repo.created) == 1


def test_list_projects_without_metrics(service):
    p1 = DummyProject(1, "a", "A")
    p2 = DummyProject(2, "b", "B")
    service.project_repo.projects = [p1, p2]
    service.project_repo.total = 22

    items, pagination = service.list_projects(connection_id=1, include_metrics=False, page=2, page_size=10)

    assert items == [p1, p2]
    assert pagination == {
        "page": 2,
        "page_size": 10,
        "total_count": 22,
        "total_pages": 3,
    }


def test_list_projects_with_metrics(service):
    p1 = DummyProject(1, "a", "A")
    service.project_repo.projects = [p1]
    service.project_repo.total = 1
    service.metrics_repo.latest[1] = {"bugs_count": 5}

    items, _ = service.list_projects(connection_id=1, include_metrics=True, page=1, page_size=20)

    assert len(items) == 1
    assert items[0]["project"] == p1
    assert items[0]["latest_metrics"] == {"bugs_count": 5}


def test_get_project_with_metrics(service):
    service.metrics_repo.latest[7] = {"coverage": 80.0}
    service.metrics_repo.branches[7] = [{"branch_name": "main"}, {"branch_name": "dev"}]

    result = service.get_project(project_id=7, include_metrics=True)

    assert result["project"].id == 7
    assert result["latest_metrics"] == {"coverage": 80.0}
    assert result["branches"] == ["main", "dev"]


def test_get_project_branches(service):
    expected = [{"branch_name": "main", "snapshot_count": 2}]
    service.metrics_repo.branches[9] = expected

    branches = service.get_project_branches(project_id=9)

    assert branches == expected
