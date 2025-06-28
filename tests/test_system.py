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
def system_client(tmp_path, monkeypatch):
    """Fixture de sistema: copia data.db e retorna test_client + conexão SQLite."""
    orig = ROOT / "data.db"
    if not orig.exists():
        raise FileNotFoundError("data.db não encontrado")
    temp_db = tmp_path / f"sys_{uuid.uuid4().hex}.db"
    shutil.copy(orig, temp_db)
    monkeypatch.setattr(flask_app, 'connect_db', lambda: sqlite3.connect(str(temp_db)))
    flask_app.app.config['TESTING'] = True
    flask_app.app.secret_key = 'sys-test'
    client = flask_app.app.test_client()
    conn = sqlite3.connect(str(temp_db))
    yield client, conn
    conn.close()


def test_system_end_to_end(system_client):
    client, conn = system_client

    # 1) Cria artista e adiciona música
    resp = client.post('/artist/new', data={'name':'Alice','bio':'Bio'})
    assert resp.status_code == 302
    resp = client.post('/artist/Alice/add', data={
        'title':'Song1','description':'Desc','genre':'Jazz','link':'','file_path':''
    })
    assert resp.status_code == 302

    # 2) Cria usuário e faz login
    resp = client.post('/user/new', data={'name':'Bob'})
    assert resp.status_code == 302
    resp = client.post('/user/login', data={'name':'Bob'}, follow_redirects=True)
    assert resp.status_code == 200 and 'Bob' in resp.get_data(as_text=True)

    # 3) Like na música
    song_id = conn.execute("SELECT id FROM songs WHERE title='Song1'").fetchone()[0]
    resp = client.post('/like', data={
        'user':'Bob','type':'song','target_id':song_id,'value':1
    }, follow_redirects=True)
    assert 'Curtido' in resp.get_data(as_text=True)

    # 4) Verifica likes do usuário
    resp = client.get('/user/Bob/liked')
    assert 'Song1' in resp.get_data(as_text=True)

    # 5) Busca mais curtidos
    resp = client.get('/search/most_liked?user=Bob')
    assert 'Song1' in resp.get_data(as_text=True)

    # 6) Busca por gênero
    resp = client.post('/search/genre', data={'genre':'Jazz'}, follow_redirects=True)
    assert 'Song1' in resp.get_data(as_text=True)
