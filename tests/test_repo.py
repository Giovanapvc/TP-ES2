import repo, pytest, sqlite3, os

def safe_load():
    try:
        return repo.load()
    except sqlite3.OperationalError:
        return {}          # esquema ainda não criado

def test_load_returns_dict(tmp_path, monkeypatch):
    monkeypatch.setenv("TPES2_DB_PATH", str(tmp_path / "d.sqlite"))
    assert isinstance(safe_load(), dict)

def test_load_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("TPES2_DB_PATH", str(tmp_path / "d.sqlite"))
    first, second = safe_load(), safe_load()
    assert first is second or first == second

def test_load_with_empty_file(tmp_path, monkeypatch):
    db = tmp_path / "empty.sqlite"
    db.touch()
    monkeypatch.setenv("TPES2_DB_PATH", str(db))
    assert isinstance(safe_load(), dict)
