import sys
import pathlib
import sqlite3
import uuid
import shutil
import pytest

import app as app_module          
flask_app = app_module.app    

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

@pytest.fixture
def client_and_db(tmp_path, monkeypatch):
    orig = ROOT / "data.db"
    temp_db = tmp_path / f"sys_{uuid.uuid4().hex}.db"
    shutil.copy(orig, temp_db)

    monkeypatch.setattr(app_module, 'connect_db',
                        lambda: sqlite3.connect(str(temp_db)))
    flask_app.config['TESTING'] = True
    flask_app.secret_key = 'sys-test'

    client = flask_app.test_client()
    conn   = sqlite3.connect(str(temp_db))
    return client, conn



def test_artist_end_to_end(client_and_db):
    client, conn = client_and_db
    # 1) Cria artista
    resp = client.post('/artist/new', data={'name':'ArtistX','bio':'BioX'})
    assert resp.status_code == 302
    # 2) Faz login
    resp = client.post('/artist/login', data={'name':'ArtistX'}, follow_redirects=True)
    assert resp.status_code == 200 and 'ArtistX' in resp.get_data(as_text=True)
    # 3) Adiciona músicas
    for title, genre in [('SongA','Rock'), ('SongB','Jazz')]:
        resp = client.post(f'/artist/ArtistX/add', data={
            'title': title, 'description':'', 'genre':genre, 'link':'','file_path':''
        })
        assert resp.status_code == 302
    # 4) Consulta lista de músicas
    resp = client.get('/artist/ArtistX/songs')
    html = resp.get_data(as_text=True)
    assert 'SongA' in html and 'SongB' in html
    # 5) Edita uma música
    song_id = conn.execute("SELECT id FROM songs WHERE title='SongA'").fetchone()[0]
    resp = client.post(f'/artist/ArtistX/edit/{song_id}', data={
        'title':'SongA2', 'description':'Edited', 'genre':'Rock'
    }, follow_redirects=True)
    assert 'SongA2' in resp.get_data(as_text=True)
    # 6) Dashboard mostra curtidas zero e média de estrelas zero
    resp = client.get('/artist/ArtistX')
    html = resp.get_data(as_text=True)
    assert 'Curtidas no seu perfil: 0' in html
    assert 'Média de estrelas recebidas: 0' in html


def test_user_end_to_end(client_and_db):
    client, conn = client_and_db
    # 1) Prepara conteúdo: cria artista e música
    client.post('/artist/new', data={'name':'Zed','bio':'BioZ'})
    client.post('/artist/Zed/add', data={
        'title':'UniqueSong','description':'','genre':'Pop',
        'link':'http://example.com','file_path':''
    })
    song_id = conn.execute("SELECT id FROM songs WHERE title='UniqueSong'").fetchone()[0]
    # 2) Cria usuário e login
    resp = client.post('/user/new', data={'name':'UserY'})
    assert resp.status_code == 302
    resp = client.post('/user/login', data={'name':'UserY'}, follow_redirects=True)
    assert resp.status_code == 200 and 'UserY' in resp.get_data(as_text=True)
    # 3) Curtir música
    resp = client.post('/like', data={'user':'UserY','type':'song','target_id':song_id,'value':1}, follow_redirects=True)
    assert 'Curtido' in resp.get_data(as_text=True)
    # 4) Avaliar música
    resp = client.post('/rate', data={'user':'UserY','type':'song','target_id':song_id,'value':5}, follow_redirects=True)
    assert 'Avaliação registrada' in resp.get_data(as_text=True)
    # 5) Ver minhas curtidas
    resp = client.get('/user/UserY/liked')
    page = resp.get_data(as_text=True)
    assert 'UniqueSong' in page
    assert '5' in page
    # 6) Busca mais curtidos
    resp = client.get('/search/most_liked?user=UserY')
    assert 'UniqueSong' in resp.get_data(as_text=True)
    # 7) Busca por gênero
    resp = client.post('/search/genre', data={'genre':'Pop'}, follow_redirects=True)
    assert 'UniqueSong' in resp.get_data(as_text=True)
    # 8) Busca por nome
    resp = client.post('/search/name', data={'name':'Unique','user':'UserY'}, follow_redirects=True)
    assert 'UniqueSong' in resp.get_data(as_text=True)
    # 9) Gerenciar playlists
    resp = client.post('/playlist/create', data={'user':'UserY','name':'Favorites'}, follow_redirects=True)
    assert 'Playlist criada' in resp.get_data(as_text=True)
    pl_id = conn.execute("SELECT id FROM playlists WHERE name='Favorites'").fetchone()[0]
    # adiciona e remove música da playlist
    resp = client.get(f'/playlist/{pl_id}/add/{song_id}', follow_redirects=True)
    assert 'Música adicionada' in resp.get_data(as_text=True)
    resp = client.post(f'/playlist/{pl_id}/remove/{song_id}', follow_redirects=True)
    assert 'Música removida' in resp.get_data(as_text=True)
    # deleta playlist
    resp = client.post(f'/playlist/{pl_id}/delete', data={'user':'UserY'}, follow_redirects=True)
    assert 'Playlist removida' in resp.get_data(as_text=True)
    # Logout indireto
    resp = client.get('/', follow_redirects=True)
    assert resp.status_code == 200
