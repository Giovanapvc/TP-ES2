import sys
import pathlib
import sqlite3
import uuid
import shutil
import tempfile
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as flask_app

@pytest.fixture
def client_with_db_copy(tmp_path, monkeypatch):
    orig = ROOT / "data.db"
    if not orig.exists():
        raise FileNotFoundError("data.db não encontrado na raiz do projeto")

    temp_db = tmp_path / f"test_{uuid.uuid4().hex}.db"
    shutil.copy(orig, temp_db)

    monkeypatch.setattr(flask_app, 'connect_db', lambda: sqlite3.connect(str(temp_db)))

    flask_app.app.config['TESTING'] = True
    flask_app.app.secret_key = 'test'

    yield flask_app.app.test_client(), sqlite3.connect(str(temp_db))

def test_connect_db_returns_connection():
    """A função connect_db deve retornar uma conexão sqlite3"""
    conn = flask_app.connect_db()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_index_page(client_with_db_copy):
    client, _ = client_with_db_copy
    assert client.get("/").status_code == 200


def test_artist_initial_screen(client_with_db_copy):
    client, _ = client_with_db_copy
    assert client.get("/artist").status_code == 200


def test_create_artist_redirects(client_with_db_copy):
    client, conn = client_with_db_copy
    before = conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0]
    resp = client.post("/artist/new", data={"name": "A", "bio": "B"})
    after = conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0]
    assert resp.status_code == 302
    assert after == before + 1


def test_artist_login_success(client_with_db_copy):
    client, _ = client_with_db_copy
    client.post("/artist/new", data={"name": "Art", "bio": ""})
    resp = client.post("/artist/login", data={"name": "Art"}, follow_redirects=True)
    assert resp.status_code == 200
    assert "Art" in resp.get_data(as_text=True)


def test_artist_login_fail_flash(client_with_db_copy):
    client, _ = client_with_db_copy
    resp = client.post("/artist/login", data={"name": "X"}, follow_redirects=True)
    assert "Artista" in resp.get_data(as_text=True)


def test_add_song(client_with_db_copy):
    client, conn = client_with_db_copy
    client.post("/artist/new", data={"name": "Au", "bio": ""})
    before = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
    client.post("/artist/Au/add", data={
        'title': 'T', 'description': 'd', 'genre': 'Pop', 'link': '', 'file_path': ''
    })
    after = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
    assert after == before + 1


def test_list_songs_contains_title(client_with_db_copy):
    client, _ = client_with_db_copy
    client.post("/artist/new", data={"name": "Z", "bio": ""})
    client.post("/artist/Z/add", data={
        'title': 'XYZ123', 'description': '', 'genre': 'Pop', 'link': '', 'file_path': ''
    })
    resp = client.get("/artist/Z/songs")
    assert "XYZ123" in resp.get_data(as_text=True)


def test_edit_song_changes_title(client_with_db_copy):
    client, conn = client_with_db_copy
    client.post("/artist/new", data={"name": "Q", "bio": ""})
    client.post("/artist/Q/add", data={
        'title': 'Old', 'description': '', 'genre': 'Rock', 'link': '', 'file_path': ''
    })
    song_id = conn.execute("SELECT id FROM songs WHERE title='Old'").fetchone()[0]
    client.post(f"/artist/Q/edit/{song_id}", data={
        'title': 'New', 'description': '', 'genre': 'Rock'
    })
    new_title = conn.execute("SELECT title FROM songs WHERE id=?", (song_id,)).fetchone()[0]
    assert new_title == 'New'


def test_create_user_and_redirect(client_with_db_copy):
    client, conn = client_with_db_copy
    before = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    resp = client.post("/user/new", data={"name": "U"})
    after = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert resp.status_code == 302 and after == before + 1


def test_user_login_success(client_with_db_copy):
    client, _ = client_with_db_copy
    client.post("/user/new", data={"name": "Jo"})
    resp = client.post("/user/login", data={"name": "Jo"}, follow_redirects=True)
    assert resp.status_code == 200 and "Jo" in resp.get_data(as_text=True)


def test_user_login_fail_flash(client_with_db_copy):
    client, _ = client_with_db_copy
    resp = client.post("/user/login", data={"name": "Nope"}, follow_redirects=True)
    assert "Usuário" in resp.get_data(as_text=True)


def test_like_song_creates_and_unlike_deletes(client_with_db_copy):
    client, conn = client_with_db_copy
    client.post("/artist/new", data={"name": "A", "bio": ""})
    client.post("/artist/A/add", data={
        'title': 'SongT', 'description': '', 'genre': 'Pop', 'link': '', 'file_path': ''
    })
    song_id = conn.execute("SELECT id FROM songs WHERE title='SongT'").fetchone()[0]
    client.post("/user/new", data={"name": "U"})
    before = conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0]
    client.post("/like", data={
        'user': 'U', 'type': 'song', 'target_id': song_id, 'value': 1
    })
    after_like = conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0]
    assert after_like == before + 1
    client.post("/like", data={
        'user': 'U', 'type': 'song', 'target_id': song_id, 'value': 0
    })
    after_unlike = conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0]
    assert after_unlike == before


def test_most_liked_page_loads(client_with_db_copy):
    client, _ = client_with_db_copy
    assert client.get("/search/most_liked").status_code == 200


def test_search_by_name_form_loads(client_with_db_copy):
    client, _ = client_with_db_copy
    assert "name" in client.get("/search/name").get_data(as_text=True)


def test_artist_dashboard_shows_name(client_with_db_copy):
    client, _ = client_with_db_copy
    client.post('/artist/new', data={'name': 'Art1', 'bio': 'Bio'})
    client.post('/artist/login', data={'name': 'Art1'})
    resp = client.get('/artist/Art1')
    assert resp.status_code == 200
    assert 'Art1' in resp.get_data(as_text=True)


def test_edit_song_form_loads_existing_data(client_with_db_copy):
    client, conn = client_with_db_copy
    client.post('/artist/new', data={'name': 'Ed', 'bio': ''})
    client.post('/artist/login', data={'name': 'Ed'})
    client.post('/artist/Ed/add', data={
        'title': 'OldTitle', 'description': 'Desc', 'genre': 'Rock',
        'link': '', 'file_path': ''
    })
    song_id = conn.execute("SELECT id FROM songs WHERE title = 'OldTitle'").fetchone()[0]
    resp = client.get(f'/artist/Ed/edit/{song_id}')
    assert resp.status_code == 200
    assert 'value="OldTitle"' in resp.get_data(as_text=True)


def test_search_by_name_returns_song_and_artist(client_with_db_copy):
    client, conn = client_with_db_copy
    client.post('/artist/new', data={'name': 'FindMe', 'bio': ''})
    client.post('/artist/login', data={'name': 'FindMe'})
    client.post('/artist/FindMe/add', data={
        'title': 'UniqueSong', 'description': '', 'genre': 'Pop',
        'link': '', 'file_path': ''
    })
    client.post('/user/new', data={'name': 'Seeker'})
    client.post('/user/login', data={'name': 'Seeker'})
    resp = client.post('/search/name', data={'name': 'Unique', 'user': 'Seeker'}, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'UniqueSong' in html
    assert 'FindMe' in html
