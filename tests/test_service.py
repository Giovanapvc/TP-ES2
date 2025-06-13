import repo, service, sqlite3, pytest

def new_store(tmp_path, monkeypatch):
    monkeypatch.setenv("TPES2_DB_PATH", str(tmp_path / "s.sqlite"))
    try:
        return repo.load()
    except sqlite3.OperationalError:
        return {}           # store vazio

def test_add_and_find_artist(tmp_path, monkeypatch):
    store = new_store(tmp_path, monkeypatch)
    art  = service.add_artist(store, "Neo")
    same = service.find_artist_by_name(store, "Neo")
    assert same and art.id == same.id

def test_add_song(tmp_path, monkeypatch):
    store = new_store(tmp_path, monkeypatch)
    art = service.add_artist(store, "Trinity")
    song = service.add_song(store, art.id, "Matrix", "", "Rock", "", "")
    assert song.title == "Matrix"

def test_like_song(tmp_path, monkeypatch):
    store = new_store(tmp_path, monkeypatch)
    art  = service.add_artist(store, "Morpheus")
    song = service.add_song(store, art.id, "Dream", "", "Pop", "", "")
    before = song.likes
    service.like_song(store, art.id, song.id)
    assert song.likes == before + 1
