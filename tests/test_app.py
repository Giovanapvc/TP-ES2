# tests/test_app.py
import sys, pathlib, sqlite3, uuid, shutil, tempfile

# Permite importar app.py mesmo rodando testes dentro de tests/
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as flask_app

# Fixture utilitária: copia data.db para um temp, monkey-patch connect_db
def client_with_db_copy():
    orig = ROOT / "data.db"
    if not orig.exists():
        raise FileNotFoundError("data.db não encontrado na raiz do projeto")

    # Copia data.db para um arquivo único em diretório temporário
    tmp_dir = pathlib.Path(tempfile.gettempdir())
    temp_db = tmp_dir / f"test_{uuid.uuid4().hex}.db"
    shutil.copy(orig, temp_db)

    # Faz app.connect_db usar a cópia temporária
    flask_app.connect_db = lambda: sqlite3.connect(temp_db)

    # Configura Flask em modo teste
    flask_app.app.config["TESTING"] = True
    flask_app.app.secret_key = "test"

    # Retorna test-client e conexão aberta para inspeção
    return flask_app.app.test_client(), sqlite3.connect(temp_db)


def test_index_page():
    # Verifica se a rota raiz retorna HTTP 200
    client, _ = client_with_db_copy()
    assert client.get("/").status_code == 200


def test_artist_initial_screen():
    # Verifica tela inicial do fluxo de artista
    client, _ = client_with_db_copy()
    assert client.get("/artist").status_code == 200


def test_create_artist_redirects():
    # Garante redirecionamento e inserção de artista
    client, conn = client_with_db_copy()
    before = conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0]
    r = client.post("/artist/new", data={"name": "A", "bio": "B"})
    after = conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0]
    assert r.status_code == 302
    assert after == before + 1


def test_artist_login_success():
    # Testa login bem-sucedido de artista
    client, _ = client_with_db_copy()
    client.post("/artist/new", data={"name": "Art", "bio": ""})
    r = client.post("/artist/login", data={"name": "Art"}, follow_redirects=True)
    assert r.status_code == 200
    assert "Art" in r.get_data(as_text=True)


def test_artist_login_fail_flash():
    # Testa flash de erro ao tentar login com nome inválido
    client, _ = client_with_db_copy()
    r = client.post("/artist/login", data={"name": "X"}, follow_redirects=True)
    assert "Artista" in r.get_data(as_text=True)


def test_add_song():
    # Verifica inserção de música no DB
    client, conn = client_with_db_copy()
    client.post("/artist/new", data={"name": "Au", "bio": ""})
    before = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
    client.post("/artist/Au/add",
                data=dict(title="T", description="d", genre="Pop",
                          link="", file_path=""))
    after = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
    assert after == before + 1


def test_list_songs_contains_title():
    # Garante que a listagem mostra o título adicionado
    client, _ = client_with_db_copy()
    client.post("/artist/new", data={"name": "Z", "bio": ""})
    client.post("/artist/Z/add",
                data=dict(title="XYZ123", description="", genre="Pop",
                          link="", file_path=""))
    r = client.get("/artist/Z/songs")
    assert "XYZ123" in r.get_data(as_text=True)


def test_edit_song_changes_title():
    # Testa edição de título de música existente
    client, conn = client_with_db_copy()
    client.post("/artist/new", data={"name": "Q", "bio": ""})
    client.post("/artist/Q/add",
                data=dict(title="Old", description="", genre="Rock",
                          link="", file_path=""))
    song_id = conn.execute("SELECT id FROM songs WHERE title='Old'").fetchone()[0]
    client.post(f"/artist/Q/edit/{song_id}",
                data=dict(title="New", description="", genre="Rock"))
    new_title = conn.execute("SELECT title FROM songs WHERE id=?", (song_id,)).fetchone()[0]
    assert new_title == "New"


def test_create_user_and_redirect():
    # Garante criação de usuário e redirecionamento
    client, conn = client_with_db_copy()
    before = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    r = client.post("/user/new", data={"name": "U"})
    after = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert r.status_code == 302 and after == before + 1


def test_user_login_success():
    # Testa login de usuário válido
    client, _ = client_with_db_copy()
    client.post("/user/new", data={"name": "Jo"})
    r = client.post("/user/login", data={"name": "Jo"}, follow_redirects=True)
    assert r.status_code == 200 and "Jo" in r.get_data(as_text=True)


def test_user_login_fail_flash():
    # Testa flash ao login de usuário inválido
    client, _ = client_with_db_copy()
    r = client.post("/user/login", data={"name": "Nope"}, follow_redirects=True)
    assert "Usuário" in r.get_data(as_text=True)


def test_like_song_creates_and_unlike_deletes():
    # Verifica fluxo de like/unlike na tabela likes
    client, conn = client_with_db_copy()
    client.post("/artist/new", data={"name": "A", "bio": ""})
    client.post("/artist/A/add",
                data=dict(title="SongT", description="", genre="Pop",
                          link="", file_path=""))
    song_id = conn.execute("SELECT id FROM songs WHERE title='SongT'").fetchone()[0]
    client.post("/user/new", data={"name": "U"})
    before = conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0]
    client.post("/like", data=dict(user="U", type="song",
                                       target_id=song_id, value=1))
    after_like = conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0]
    assert after_like == before + 1
    client.post("/like", data=dict(user="U", type="song",
                                       target_id=song_id, value=0))
    after_unlike = conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0]
    assert after_unlike == before


def test_most_liked_page_loads():
    # Verifica rota /search/most_liked responde 200
    client, _ = client_with_db_copy()
    assert client.get("/search/most_liked").status_code == 200


def test_search_by_name_form_loads():
    # Verifica página de formulário de busca por nome
    client, _ = client_with_db_copy()
    assert "name" in client.get("/search/name").get_data(as_text=True)


def test_search_by_genre_filters_and_persists():
    # Valida busca por gênero e persistência em sessão
    client, conn = client_with_db_copy()
    client.post("/artist/new", data={"name": "TheBand", "bio": "..."})
    client.post("/artist/TheBand/add",
                data=dict(title="PopHit", description="", genre="Pop",
                          link="", file_path=""))
    client.post("/artist/TheBand/add",
                data=dict(title="RockHit", description="", genre="Rock",
                          link="", file_path=""))
    client.post("/user/new", data={"name": "Fan"})
    client.post("/user/login", data={"name": "Fan"}, follow_redirects=True)

    resp = client.post("/search/genre",
                       data={"genre": "Pop"}, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "PopHit" in html
    assert "RockHit" not in html
    assert "TheBand" in html
    with client.session_transaction() as sess:
        assert sess.get("last_genres") == ["Pop"]
