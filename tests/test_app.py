# tests/test_app.py
import sys, pathlib, sqlite3, uuid

# --- permitir "import app" mesmo quando o pytest roda dentro de tests/ ----------
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as flask_app

# ---------- DDL de teste ----------
SCHEMA = """
CREATE TABLE artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    bio  TEXT
);
CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id INTEGER,
    title TEXT,
    description TEXT,
    genre TEXT,
    link TEXT,
    file_path TEXT
);
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
);
CREATE TABLE likes (
    user TEXT,
    type TEXT,
    target_id INTEGER,
    value INTEGER,
    PRIMARY KEY (user, type, target_id)
);
"""

# ---------- fixture utilitária ----------
def client_with_fresh_db():
    """
    Devolve (client, inspect_conn) usando um banco em memória exclusivo.
    Cada rota abre a própria conexão, mas todas compartilham o mesmo
    banco via URI `file:<uuid>?mode=memory&cache=shared`.
    """
    uri = f"file:{uuid.uuid4().hex}?mode=memory&cache=shared"

    # cria schema
    seed = sqlite3.connect(uri, uri=True)
    seed.executescript(SCHEMA)
    seed.commit()

    # app.connect_db sempre aponta para esse URI
    flask_app.connect_db = lambda: sqlite3.connect(uri, uri=True)

    flask_app.app.config["TESTING"] = True
    flask_app.app.secret_key = "test-secret"
    return flask_app.app.test_client(), seed


# ---------- 15 TESTES ---------------------------------------------------------

def test_index_page():
    client, _ = client_with_fresh_db()
    assert client.get("/").status_code == 200


def test_artist_initial_screen():
    client, _ = client_with_fresh_db()
    assert client.get("/artist").status_code == 200


def test_create_artist_redirects():
    client, conn = client_with_fresh_db()
    r = client.post("/artist/new", data={"name": "A", "bio": "B"})
    assert r.status_code == 302
    assert conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0] == 1


def test_artist_login_success():
    client, _ = client_with_fresh_db()
    client.post("/artist/new", data={"name": "A", "bio": ""})
    r = client.post("/artist/login", data={"name": "A"}, follow_redirects=True)
    assert r.status_code == 200
    assert "A" in r.get_data(as_text=True)


def test_artist_login_fail_flash():
    client, _ = client_with_fresh_db()
    r = client.post("/artist/login", data={"name": "X"}, follow_redirects=True)
    assert "Artista" in r.get_data(as_text=True)


def test_add_song():
    client, conn = client_with_fresh_db()
    client.post("/artist/new", data={"name": "A", "bio": ""})
    client.post("/artist/A/add",
                data=dict(title="T", description="d", genre="Pop",
                          link="", file_path=""))
    assert conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0] == 1


def test_list_songs_contains_title():
    client, _ = client_with_fresh_db()
    client.post("/artist/new", data={"name": "Z", "bio": ""})
    client.post("/artist/Z/add",
                data=dict(title="X", description="", genre="Pop",
                          link="", file_path=""))
    r = client.get("/artist/Z/songs")
    assert "X" in r.get_data(as_text=True)


def test_edit_song_changes_title():
    client, conn = client_with_fresh_db()
    client.post("/artist/new", data={"name": "Q", "bio": ""})
    client.post("/artist/Q/add",
                data=dict(title="Old", description="", genre="Rock",
                          link="", file_path=""))
    song_id = conn.execute("SELECT id FROM songs").fetchone()[0]
    client.post(f"/artist/Q/edit/{song_id}",
                data=dict(title="New", description="", genre="Rock"))
    assert conn.execute("SELECT title FROM songs").fetchone()[0] == "New"


def test_create_user_and_redirect():
    client, conn = client_with_fresh_db()
    r = client.post("/user/new", data={"name": "U"})
    assert r.status_code == 302
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1


def test_user_login_success():
    client, _ = client_with_fresh_db()
    client.post("/user/new", data={"name": "Jo"})
    r = client.post("/user/login", data={"name": "Jo"}, follow_redirects=True)
    assert r.status_code == 200
    assert "Jo" in r.get_data(as_text=True)


def test_user_login_fail_flash():
    client, _ = client_with_fresh_db()
    r = client.post("/user/login", data={"name": "Nope"}, follow_redirects=True)
    assert "Usuário" in r.get_data(as_text=True)


def test_like_song_creates_row():
    client, conn = client_with_fresh_db()
    client.post("/artist/new", data={"name": "A", "bio": ""})
    client.post("/artist/A/add",
                data=dict(title="S", description="", genre="Pop",
                          link="", file_path=""))
    song_id = conn.execute("SELECT id FROM songs").fetchone()[0]
    client.post("/user/new", data={"name": "U"})
    client.post("/like", data=dict(user="U", type="song",
                                   target_id=song_id, value=1))
    assert conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0] == 1


def test_unlike_song_deletes_row():
    client, conn = client_with_fresh_db()
    client.post("/artist/new", data={"name": "A", "bio": ""})
    client.post("/artist/A/add",
                data=dict(title="S", description="", genre="Pop",
                          link="", file_path=""))
    song_id = conn.execute("SELECT id FROM songs").fetchone()[0]
    client.post("/user/new", data={"name": "U"})
    client.post("/like", data=dict(user="U", type="song",
                                   target_id=song_id, value=1))
    client.post("/like", data=dict(user="U", type="song",
                                   target_id=song_id, value=0))
    assert conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0] == 0


def test_most_liked_page_loads():
    client, _ = client_with_fresh_db()
    assert client.get("/search/most_liked").status_code == 200


def test_search_by_name_form_loads():
    client, _ = client_with_fresh_db()
    assert "name" in client.get("/search/name").get_data(as_text=True)
