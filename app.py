from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'teste123'

def connect_db():
    """Retorna uma conexão puros sqlite."""
    return sqlite3.connect('data.db')

def get_conn():
    """Retorna uma conexão com row_factory configurado para sqlite3.Row."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/song/<int:song_id>')
def song_detail(song_id):
    return redirect(url_for('index'))


@app.route('/artist')
def artist_initial_screen():
    return render_template('artists/artist_initial_screen.html')

@app.route('/artist/new', methods=['GET', 'POST'])
def create_artist():
    if request.method == 'POST':
        name = request.form['name']
        bio  = request.form['bio']
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO artists (name, bio) VALUES (?, ?)", (name, bio))
        conn.commit(); conn.close()
        return redirect(url_for('artist_login'))
    return render_template('artists/create_artist.html')

@app.route('/artist/login', methods=['GET', 'POST'])
def artist_login():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT * FROM artists WHERE name = ?", (name,))
        artist = cur.fetchone(); conn.close()
        if artist:
            session['artist'] = name
            return redirect(url_for('artist_dashboard', name=name))
        flash("Artista não encontrado")
    return render_template('artists/artist_login.html')

@app.route('/artist/<name>')
def artist_dashboard(name):
    conn = get_conn(); cur = conn.cursor()

    # busca dados do artista
    cur.execute("SELECT id, bio FROM artists WHERE name = ?", (name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return "Artista não encontrado", 404

    artist_id  = row['id']
    artist_bio = row['bio']

    # total de curtidas no perfil
    cur.execute("""
        SELECT COALESCE(SUM(value),0) AS total_artist_likes
          FROM likes
         WHERE type='artist' AND target_id=?
    """, (artist_id,))
    total_artist_likes = cur.fetchone()['total_artist_likes']

    # lista de quem curtiu
    cur.execute("""
        SELECT user
          FROM likes
         WHERE type='artist' AND target_id=? AND value=1
    """, (artist_id,))
    artist_likers = [r['user'] for r in cur.fetchall()]

    # média de estrelas recebidas
    cur.execute("""
        SELECT COALESCE(AVG(value),0) AS avg_artist_rating
          FROM ratings
         WHERE type='artist' AND target_id=?
    """, (artist_id,))
    avg_artist_rating = cur.fetchone()['avg_artist_rating']

    # total de curtidas em todas as músicas
    cur.execute("""
        SELECT COALESCE(SUM(l.value),0) AS total_song_likes
          FROM songs s
     LEFT JOIN likes l ON l.type='song' AND l.target_id=s.id
         WHERE s.artist_id=?
    """, (artist_id,))
    total_song_likes = cur.fetchone()['total_song_likes']

    conn.close()
    return render_template(
        'artists/artist_dashboard.html',
        artist=name,
        bio=artist_bio,
        total_artist_likes=total_artist_likes,
        artist_likers=artist_likers,
        avg_artist_rating=avg_artist_rating,
        total_song_likes=total_song_likes
    )

@app.route('/artist/<name>/add', methods=['GET', 'POST'])
def add_song(name):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    art = cur.fetchone()
    if not art:
        conn.close()
        return "Artista não encontrado", 404

    artist_id = art['id']
    if request.method == 'POST':
        cur.execute("""
            INSERT INTO songs (artist_id, title, description, genre, link, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            artist_id,
            request.form['title'],
            request.form['description'],
            request.form['genre'],
            request.form['link'],
            request.form['file_path'],
        ))
        conn.commit(); conn.close()
        return redirect(url_for('artist_dashboard', name=name))

    conn.close()
    return render_template('artists/add_song.html', artist=name)

@app.route('/artist/<name>/songs')
def list_songs(name):
    conn = get_conn()
    cur  = conn.cursor()

    # busca artista
    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    art = cur.fetchone()
    if not art:
        conn.close()
        return "Artista não encontrado", 404
    artist_id = art['id']

    # busca todas as músicas
    cur.execute("SELECT * FROM songs WHERE artist_id = ?", (artist_id,))
    songs = cur.fetchall()

    likers_map   = {}
    opinions_map = {}
    avg_ratings  = {}

    for s in songs:
        sid = s['id']

        # quem curtiu
        cur.execute(
            "SELECT user FROM likes WHERE type='song' AND target_id=? AND value=1",
            (sid,)
        )
        likers_map[sid] = [r['user'] for r in cur.fetchall()]

        # opiniões
        cur.execute(
            "SELECT user, text FROM opinions WHERE type='song' AND target_id=?",
            (sid,)
        )
        opinions_map[sid] = cur.fetchall()

        # média de ratings
        cur.execute(
            "SELECT COALESCE(AVG(value), 0) AS avg_rating FROM ratings WHERE type='song' AND target_id=?",
            (sid,)
        )
        avg_ratings[sid] = cur.fetchone()['avg_rating']

    conn.close()
    return render_template(
        'artists/list_songs.html',
        artist=name,
        songs=songs,
        likers_map=likers_map,
        opinions_map=opinions_map,
        avg_ratings=avg_ratings
    )

@app.route('/artist/<name>/edit/<int:id>', methods=['GET', 'POST'])
def edit_songs(name, id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    art = cur.fetchone()
    if not art:
        conn.close()
        return "Artista não encontrado", 404

    artist_id = art['id']
    if request.method == 'POST':
        cur.execute("""
            UPDATE songs
               SET title = ?, description = ?, genre = ?
             WHERE id = ? AND artist_id = ?
        """, (
            request.form['title'],
            request.form['description'],
            request.form['genre'],
            id, artist_id
        ))
        conn.commit(); conn.close()
        return redirect(url_for('list_songs', name=name))

    cur.execute("SELECT * FROM songs WHERE id = ? AND artist_id = ?", (id, artist_id))
    song = cur.fetchone(); conn.close()
    if not song:
        return "Música não encontrada", 404
    return render_template('artists/edit_songs.html', artist=name, song=song)


@app.route('/user')
def user_initial_screen():
    return render_template('users/user_initial_screen.html')

@app.route('/user/new', methods=['GET','POST'])
def create_user():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit(); conn.close()
        return redirect(url_for('user_login'))
    return render_template('users/create_user.html')

@app.route('/user/login', methods=['GET','POST'])
def user_login():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE name = ?", (name,))
        user = cur.fetchone(); conn.close()
        if user:
            session['user'] = name
            return redirect(url_for('user_dashboard', name=name))
        flash("Usuário não encontrado")
    return render_template('users/user_login.html')

@app.route('/user/<name>')
def user_dashboard(name):
    session.pop('last_genres', None)
    return render_template('users/user_dashboard.html', user=name)

@app.route('/user/<name>/liked')
def all_likes(name):
    conn = get_conn(); cur = conn.cursor()
    # músicas curtidas
    cur.execute("""
        SELECT s.id, s.title, a.name AS artist_name, s.link
          FROM songs s
          JOIN artists a ON s.artist_id = a.id
          JOIN likes l   ON l.target_id = s.id
         WHERE l.user = ? AND l.type = 'song' AND l.value = 1
    """, (name,))
    songs = cur.fetchall()

    # artistas curtidos
    cur.execute("""
        SELECT a.id, a.name
          FROM artists a
          JOIN likes l ON l.target_id = a.id
         WHERE l.user = ? AND l.type = 'artist' AND l.value = 1
    """, (name,))
    artists = cur.fetchall()

    # opiniões
    opinions_map = {}
    artist_opinions_map = {}
    for s in songs:
        cur.execute("SELECT user, text FROM opinions WHERE type='song' AND target_id = ?", (s['id'],))
        opinions_map[s['id']] = cur.fetchall()
    for a in artists:
        cur.execute("SELECT user, text FROM opinions WHERE type='artist' AND target_id = ?", (a['id'],))
        artist_opinions_map[a['id']] = cur.fetchall()

    # novas linhas: carregar ratings do usuário
    cur.execute("SELECT type, target_id, value FROM ratings WHERE user = ?", (name,))
    ratings_map = {(r['type'], r['target_id']): r['value'] for r in cur.fetchall()}

    conn.close()

    return render_template(
        'users/liked.html',
        user=name,
        songs=songs,
        artists=artists,
        opinions_map=opinions_map,
        artist_opinions_map=artist_opinions_map,
        ratings_map=ratings_map,  
    )

@app.route('/like', methods=['POST'])
def give_like():
    user      = request.form['user']
    type_     = request.form['type']
    target_id = int(request.form['target_id'])
    value     = int(request.form['value'])
    conn = get_conn(); cur = conn.cursor()
    if value == 1:
        cur.execute("""
            INSERT OR REPLACE INTO likes (user, type, target_id, value)
            VALUES (?, ?, ?, 1)
        """, (user, type_, target_id))
        flash('Curtido!')
    else:
        cur.execute("""
            DELETE FROM likes
             WHERE user = ? AND type = ? AND target_id = ?
        """, (user, type_, target_id))
        flash('Descurtido!')
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('user_dashboard', name=user))

@app.route('/opinion/song/<int:song_id>', methods=['POST'])
def opinion_song(song_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO opinions (user, type, target_id, text)
        VALUES (?, 'song', ?, ?)
    """, (
        request.form['user'],
        song_id,
        request.form['text']
    ))
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('user_dashboard', name=request.form['user']))

@app.route('/opinion/artist/<int:artist_id>', methods=['POST'])
def opinion_artist(artist_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO opinions (user, type, target_id, text)
        VALUES (?, 'artist', ?, ?)
    """, (
        request.form['user'],
        artist_id,
        request.form['text']
    ))
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('user_dashboard', name=request.form['user']))


@app.route('/search/most_liked')
def most_liked():
    session.pop('last_genres', None)
    user = request.args.get('user','')
    conn = get_conn(); cur = conn.cursor()

    # músicas mais curtidas
    cur.execute("""
        SELECT s.*, a.name AS artist_name,
               COALESCE(SUM(l.value),0) AS total_likes
          FROM songs s
     LEFT JOIN likes l   ON l.target_id = s.id AND l.type = 'song'
         JOIN artists a ON s.artist_id = a.id
      GROUP BY s.id
      ORDER BY total_likes DESC
    """)
    songs = cur.fetchall()

    # artistas mais curtidos
    cur.execute("""
        SELECT a.*, COALESCE(SUM(l.value),0) AS total_likes
          FROM artists a
     LEFT JOIN likes l   ON l.target_id = a.id AND l.type = 'artist'
      GROUP BY a.id
      ORDER BY total_likes DESC
    """)
    artists = cur.fetchall()

    # itens curtidos pelo usuário
    cur.execute("SELECT type, target_id FROM likes WHERE user = ?", (user,))
    liked_items = {(r['type'], r['target_id']) for r in cur.fetchall()}

    # opiniões
    opinions_map = {}
    artist_opinions_map = {}
    for s in songs:
        cur.execute("SELECT user, text FROM opinions WHERE type='song' AND target_id = ?", (s['id'],))
        opinions_map[s['id']] = cur.fetchall()
    for a in artists:
        cur.execute("SELECT user, text FROM opinions WHERE type='artist' AND target_id = ?", (a['id'],))
        artist_opinions_map[a['id']] = cur.fetchall()

    # avaliações
    cur.execute("SELECT type, target_id, value FROM ratings WHERE user = ?", (user,))
    ratings = {(r['type'], r['target_id']): r['value'] for r in cur.fetchall()}
    if 'last_rating' in session:
        lr = session['last_rating']
        ratings[(lr['type'], lr['target_id'])] = lr['value']

    conn.close()
    return render_template(
        'users/search_most_liked.html',
        songs=songs,
        artists=artists,
        user=user,
        liked_items=liked_items,
        opinions_map=opinions_map,
        artist_opinions_map=artist_opinions_map,
        ratings=ratings
    )

@app.route('/search/genre', methods=['GET','POST'])
def search_by_genre():
    user = session.get('user')
    if not user:
        flash("Você precisa estar logado")
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        genres = request.form.getlist('genre')
        if not genres:
            flash("Selecione ao menos um gênero")
            return render_template('users/search_by_genre_form.html', user=user)
        session['last_genres'] = genres
    else:
        genres = request.args.getlist('genres')
        if not genres:
            return render_template('users/search_by_genre_form.html', user=user)

    conn = get_conn(); cur = conn.cursor()
    ph = ','.join('?'*len(genres))
    cur.execute(f"""
        SELECT s.*, a.name AS artist_name
          FROM songs s
          JOIN artists a ON s.artist_id = a.id
         WHERE s.genre IN ({ph})
    """, genres)
    songs = cur.fetchall()
    cur.execute(f"""
        SELECT DISTINCT a.*
          FROM artists a
          JOIN songs s ON s.artist_id = a.id
         WHERE s.genre IN ({ph})
    """, genres)
    artists = cur.fetchall()

    cur.execute("SELECT type, target_id FROM likes WHERE user = ?", (user,))
    liked_items = {(r['type'], r['target_id']) for r in cur.fetchall()}

    opinions_map = {}
    artist_opinions_map = {}
    for s in songs:
        cur.execute("SELECT user, text FROM opinions WHERE type='song' AND target_id = ?", (s['id'],))
        opinions_map[s['id']] = cur.fetchall()
    for a in artists:
        cur.execute("SELECT user, text FROM opinions WHERE type='artist' AND target_id = ?", (a['id'],))
        artist_opinions_map[a['id']] = cur.fetchall()

    cur.execute("SELECT type, target_id, value FROM ratings WHERE user = ?", (user,))
    ratings = {(r['type'], r['target_id']): r['value'] for r in cur.fetchall()}
    if 'last_rating' in session:
        lr = session['last_rating']
        ratings[(lr['type'], lr['target_id'])] = lr['value']

    conn.close()
    return render_template(
        'users/search_by_genre_result.html',
        songs=songs,
        artists=artists,
        genres=genres,
        user=user,
        liked_items=liked_items,
        opinions_map=opinions_map,
        artist_opinions_map=artist_opinions_map,
        ratings=ratings
    )

@app.route('/search/genre/reset')
def reset_genre_search():
    session.pop('last_genres', None)
    return redirect(url_for('search_by_genre'))

@app.route('/search/name', methods=['GET','POST'])
def search_by_name():
    session.pop('last_genres', None)

    if request.method == 'GET':
        user = request.args.get('user')
        playlist_id = request.args.get('playlist_id')
        session.pop('last_search', None)
        session.pop('last_user', None)
        session.pop('last_playlist_id', None)
        return render_template(
            'users/search_by_name_form.html',
            user=user,
            playlist_id=playlist_id
        )
    termo       = request.form.get('name', '').strip()
    user        = request.form.get('user')
    playlist_id = request.form.get('playlist_id')

    session['last_search']      = termo
    session['last_user']        = user
    session['last_playlist_id'] = playlist_id

    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT s.*, a.name AS artist_name
          FROM songs s
          JOIN artists a ON s.artist_id = a.id
         WHERE s.title LIKE ?
    """, ('%'+termo+'%',))
    songs = cur.fetchall()

    if not playlist_id:
        cur.execute("SELECT * FROM artists WHERE name LIKE ?", ('%'+termo+'%',))
        artists = cur.fetchall()
    else:
        artists = []
    likers_map = {}
    for s in songs:
        cur.execute(
            "SELECT user FROM likes WHERE type='song' AND target_id=? AND value=1",
            (s['id'],)
        )
        likers_map[('song', s['id'])] = [r['user'] for r in cur.fetchall()]
    cur.execute("SELECT type, target_id FROM likes WHERE user = ?", (user,))
    liked_items = {(r['type'], r['target_id']) for r in cur.fetchall()}
    opinions_map = {}
    for s in songs:
        cur.execute("SELECT user, text FROM opinions WHERE type='song' AND target_id = ?", (s['id'],))
        opinions_map[s['id']] = cur.fetchall()

    artist_opinions_map = {}
    for a in artists:
        cur.execute("SELECT user, text FROM opinions WHERE type='artist' AND target_id = ?", (a['id'],))
        artist_opinions_map[a['id']] = cur.fetchall()


    cur.execute("SELECT type, target_id, value FROM ratings WHERE user = ?", (user,))
    ratings = {(r['type'], r['target_id']): r['value'] for r in cur.fetchall()}

    songs_in_playlist = set()
    if playlist_id:
        cur.execute("SELECT song_id FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
        songs_in_playlist = {r['song_id'] for r in cur.fetchall()}

    conn.close()

    if playlist_id:
        back_url = url_for('view_playlist', playlist_id=playlist_id)
    else:
        back_url = url_for('user_dashboard', name=user)

    return render_template(
        'users/search_by_name_results.html',
        songs=songs,
        artists=artists,
        termo=termo,
        user=user,
        liked_items=liked_items,
        opinions_map=opinions_map,
        artist_opinions_map=artist_opinions_map,
        ratings=ratings,
        playlist_id=playlist_id,
        songs_in_playlist=songs_in_playlist,
        likers_map=likers_map,
        back_url=back_url
    )

@app.route('/rate', methods=['POST'])
def give_rating():
    user      = request.form['user']
    type_     = request.form['type']
    target_id = int(request.form['target_id'])
    value     = int(request.form['value'])
    conn = connect_db(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO ratings (user, type, target_id, value)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user, type, target_id) DO UPDATE SET value=excluded.value
    """, (user, type_, target_id, value))
    conn.commit(); conn.close()
    session['last_rating'] = dict(user=user, type=type_, target_id=target_id, value=value)
    flash('Avaliação registrada!')
    dest = request.referrer or url_for('user_dashboard', name=user)
    return redirect(dest)


@app.route('/playlists')
def user_playlists():
    user = request.args.get('user')
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM playlists WHERE user = ?", (user,))
    playlists = cur.fetchall()
    conn.close()
    return render_template('users/playlists.html', playlists=playlists, user=user)

@app.route('/playlist/create', methods=['POST'])
def create_playlist():
    user = request.form['user']
    name = request.form['name']

    conn = connect_db()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO playlists (user, name) VALUES (?, ?)", (user, name)
    )
    conn.commit()
    conn.close()

    flash('Playlist criada!')
    return redirect(url_for('user_playlists', user=user))

@app.route('/playlist/<int:playlist_id>')
def view_playlist(playlist_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
    playlist = cur.fetchone()
    cur.execute("""
        SELECT songs.*, artists.name AS artist_name
          FROM playlist_songs
          JOIN songs   ON playlist_songs.song_id = songs.id
          JOIN artists ON songs.artist_id   = artists.id
         WHERE playlist_songs.playlist_id = ?
    """, (playlist_id,))
    songs = cur.fetchall()
    cur.execute("SELECT song_id FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
    songs_in_playlist = {r['song_id'] for r in cur.fetchall()}
    conn.close()
    return render_template(
        'users/playlist_detail.html',
        playlist=playlist,
        songs=songs,
        user=playlist['user'],
        songs_in_playlist=songs_in_playlist
    )

@app.route('/playlist/<int:playlist_id>/add/<int:song_id>')
def add_song_to_playlist(playlist_id, song_id):
    conn = connect_db(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
                (playlist_id, song_id))
    conn.commit(); conn.close()
    flash('Música adicionada à playlist!')

    dest = request.referrer or url_for('view_playlist', playlist_id=playlist_id)
    return redirect(dest)

@app.route('/playlist/<int:playlist_id>/remove/<int:song_id>', methods=['POST'])
def remove_song_from_playlist(playlist_id, song_id):
    conn = connect_db(); cur = conn.cursor()
    cur.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?", (playlist_id, song_id))
    conn.commit(); conn.close()
    flash('Música removida da playlist!')
    return redirect(url_for('view_playlist', playlist_id=playlist_id))

@app.route('/user/liked/for_playlist')
def user_liked_for_playlist():
    user = request.args.get('user')
    playlist_id = request.args.get('playlist_id')
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT songs.*, artists.name AS artist_name
          FROM likes
          JOIN songs   ON songs.id   = likes.target_id
          JOIN artists ON songs.artist_id = artists.id
         WHERE likes.user = ? AND likes.type = 'song' AND likes.value = 1
    """, (user,))
    songs = cur.fetchall()
    cur.execute("SELECT song_id FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
    songs_in_playlist = {r['song_id'] for r in cur.fetchall()}
    conn.close()
    return render_template(
        'users/add_from_liked.html',
        songs=songs,
        user=user,
        playlist_id=playlist_id,
        songs_in_playlist=songs_in_playlist
    )

@app.route('/playlist/<int:playlist_id>/delete', methods=['POST'])
def delete_playlist(playlist_id):
    user = request.form['user']
    conn = connect_db(); cur = conn.cursor()
    cur.execute("DELETE FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
    cur.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
    conn.commit(); conn.close()
    flash('Playlist removida com sucesso!')
    return redirect(url_for('user_playlists', user=user))

if __name__ == '__main__':
    app.run(debug=True)
