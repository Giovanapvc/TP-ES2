import pytest, service, repo, sqlite3, os

@pytest.fixture
def store(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr(repo, "DB_FILE", db)
    repo._init()
    return {}

def test_unique_name(store):
    service.add_artist(store,"Name")
    with pytest.raises(ValueError):
        service.add_artist(store,"name")  # case-insensitive duplicate

def test_find_artist(store):
    a=service.add_artist(store,"Cool")
    assert service.find_artist_by_name(store,"cool") is a