"""Unit tests for ConnectionRepository."""

import pytest

from backend.src.db.init import init_db
from backend.src.db.base import get_db
from backend.src.db.repositories.connection_repository import ConnectionRepository
from backend.src.utils.errors import ConflictError, NotFoundError, DatabaseError


@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "test_connection_repo.db"
    init_db(str(db_path))
    db = next(get_db())
    repository = ConnectionRepository(db)
    try:
        yield repository
    finally:
        db.close()


def test_create_and_get_by_id(repo):
    created = repo.create(
        name="Main SQ",
        server_url="https://sq.local",
        server_version="9.9.0",
        organization="my-org",
    )

    fetched = repo.get_by_id(created.id)

    assert fetched.id == created.id
    assert fetched.name == "Main SQ"
    assert fetched.server_url == "https://sq.local"
    assert fetched.organization == "my-org"


def test_create_duplicate_name_raises_conflict(repo):
    repo.create(name="Dup", server_url="https://a.local")

    with pytest.raises(ConflictError):
        repo.create(name="Dup", server_url="https://b.local")


def test_get_by_id_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get_by_id(9999)


def test_get_all_and_get_by_name(repo):
    repo.create(name="One", server_url="https://one.local")
    repo.create(name="Two", server_url="https://two.local")

    all_items = repo.get_all()
    by_name = repo.get_by_name("Two")
    missing = repo.get_by_name("Missing")

    assert len(all_items) >= 2
    assert by_name is not None
    assert by_name.name == "Two"
    assert missing is None


def test_update_fields(repo):
    created = repo.create(name="Updatable", server_url="https://old.local")

    updated = repo.update(
        created.id,
        name="Updated",
        server_url="https://new.local",
        server_version="10.0.0",
        organization="new-org",
        is_active=False,
    )

    assert updated.name == "Updated"
    assert updated.server_url == "https://new.local"
    assert updated.server_version == "10.0.0"
    assert updated.organization == "new-org"
    assert updated.is_active is False


def test_update_duplicate_name_raises_conflict(repo):
    c1 = repo.create(name="First", server_url="https://first.local")
    repo.create(name="Second", server_url="https://second.local")

    with pytest.raises(ConflictError):
        repo.update(c1.id, name="Second")


def test_update_validation_timestamp(repo):
    created = repo.create(name="Validation", server_url="https://valid.local")

    updated = repo.update_validation_timestamp(created.id, server_version="9.9.1")

    assert updated.last_validated_at is not None
    assert updated.server_version == "9.9.1"


def test_delete_connection(repo):
    created = repo.create(name="DeleteMe", server_url="https://delete.local")

    repo.delete(created.id)

    with pytest.raises(NotFoundError):
        repo.get_by_id(created.id)


def test_delete_nonexistent_raises_database_error(repo):
    with pytest.raises(DatabaseError):
        repo.delete(123456)
