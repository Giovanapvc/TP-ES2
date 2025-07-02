from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'teste123'

def connect_db():
    # pytest fará monkey‐patch para apontar pro banco de teste
    return sqlite3.connect('data.db')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/song/<int:song_id>')
def song_detail(song_id):
    return redirect(url_for('index'))

# ========== ARTIST FLOW ==========

@app.route('/artist')
def artist_initial_screen():
    return render_template('artists/artist_initial_screen.html')

@app.route('/artist/new', methods=['GET', 'POST'])
def create_artist():
    if request.method == 'POST':
        name = request.form['name']
        bio  = request.form['bio']
        conn = connect_db(); cur = conn.cursor()
        cur.execute("INSERT INTO artists (name, bio) VALUES (?, ?)", (name, bio))
        conn.commit(); conn.close()
        return redirect(url_for('artist_login'))
    return render_template('artists/create_artist.html')

@app.route('/artist/login', methods=['GET', 'POST'])
def artist_login():
    if request.method == 'POST':
        name = request.form['name']
        conn = connect_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM artists WHERE name = ?", (name,))
        artist = cur.fetchone(); conn.close()
        if artist:
            session['artist'] = name
            return redirect(url_for('artist_dashboard', name=name))
        flash("Artista não encontrado")
    return render_template('artists/artist_login.html')

@app.route('/artist/<name>')
def artist_dashboard(name):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, bio FROM artists WHERE name = ?", (name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return "Artista não encontrado", 404

    artist_id  = row['id']
    artist_bio = row['bio']

    cur.execute("""
        SELECT COALESCE(SUM(value), 0) AS total_artist_likes
          FROM likes
         WHERE type = 'artist' AND target_id = ?
    """, (artist_id,))
    total_artist_likes = cur.fetchone()['total_artist_likes']

    cur.execute("""
        SELECT COALESCE(SUM(l.value), 0) AS total_song_likes
          FROM songs s
     LEFT JOIN likes l
            ON l.type = 'song' AND l.target_id = s.id
         WHERE s.artist_id = ?
    """, (artist_id,))
    total_song_likes = cur.fetchone()['total_song_likes']

    # mapas vazios para não quebrar o template
    opinions_map = {}
    likers_map   = {}

    conn.close()
    return render_template(
        'artists/artist_dashboard.html',
        artist=name,
        bio=artist_bio,
        total_artist_likes=total_artist_likes,
        total_song_likes=total_song_likes,
        opinions_map=opinions_map,
        likers_map=likers_map
    )

@app.route('/artist/<name>/opinions')
def artist_opinions(name):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # pega o artista
    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    art = cur.fetchone()
    if not art:
        conn.close()
        return "Artista não encontrado", 404
    artist_id = art['id']

    # opiniões sobre as músicas dele
    cur.execute("""
        SELECT o.user, o.text, s.title
          FROM opinions o
    JOIN songs s ON o.target_id = s.id AND o.type='song'
         WHERE s.artist_id = ?
    """, (artist_id,))
    song_opinions = cur.fetchall()

    # opiniões sobre o perfil dele
    cur.execute("""
        SELECT user, text
          FROM opinions
         WHERE type='artist' AND target_id=?
    """, (artist_id,))
    artist_opinions = cur.fetchall()

    conn.close()
    return render_template(
        'artists/opinions.html',
        artist=name,
        song_opinions=song_opinions,
        artist_opinions=artist_opinions
    )


@app.route('/artist/<name>/add', methods=['GET', 'POST'])
def add_song(name):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
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
            request.form['file_path']
        ))
        conn.commit(); conn.close()
        return redirect(url_for('artist_dashboard', name=name))

    conn.close()
    return render_template('artists/add_song.html', artist=name)

@app.route('/artist/<name>/songs')
def list_songs(name):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # pega o artista
    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    art = cur.fetchone()
    if not art:
        conn.close()
        return "Artista não encontrado", 404
    artist_id = art['id']

    # busca as músicas
    cur.execute("SELECT * FROM songs WHERE artist_id = ?", (artist_id,))
    songs = cur.fetchall()

    # quem curtiu cada música
    likers_map = {}
    for s in songs:
        cur.execute("""
            SELECT user
              FROM likes
             WHERE type='song' AND target_id=? AND value=1
        """, (s['id'],))
        likers_map[s['id']] = [r['user'] for r in cur.fetchall()]

    conn.close()
    return render_template(
        'artists/list_songs.html',
        artist=name,
        songs=songs,
        likers_map=likers_map
    )


@app.route('/artist/<name>/edit/<int:id>', methods=['GET', 'POST'])
def edit_songs(name, id):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
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
            id,
            artist_id
        ))
        conn.commit(); conn.close()
        return redirect(url_for('list_songs', name=name))

    cur.execute("SELECT * FROM songs WHERE id = ? AND artist_id = ?", (id, artist_id))
    song = cur.fetchone(); conn.close()
    if not song:
        return "Música não encontrada", 404
    return render_template('artists/edit_songs.html', artist=name, song=song)


# ========== USER FLOW ==========

@app.route('/user')
def user_initial_screen():
    return render_template('users/user_initial_screen.html')

@app.route('/user/new', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        name = request.form['name']
        conn = connect_db(); cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit(); conn.close()
        return redirect(url_for('user_login'))
    return render_template('users/create_user.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        name = request.form['name']
        conn = connect_db(); cur = conn.cursor()
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
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # pega músicas curtidas
    cur.execute("""
        SELECT s.id, s.title, a.name AS artist_name, s.link
          FROM songs s
          JOIN artists a ON s.artist_id = a.id
          JOIN likes l   ON l.target_id = s.id
         WHERE l.user = ? AND l.type = 'song' AND l.value = 1
    """, (name,))
    songs = cur.fetchall()

    # pega artistas curtidos
    cur.execute("""
        SELECT a.id, a.name
          FROM artists a
          JOIN likes l ON l.target_id = a.id
         WHERE l.user = ? AND l.type = 'artist' AND l.value = 1
    """, (name,))
    artists = cur.fetchall()

    # liked_items para botão
    cur.execute("SELECT type, target_id FROM likes WHERE user = ?", (name,))
    liked_items = {(r['type'], r['target_id']) for r in cur.fetchall()}

    # opiniões sobre músicas
    song_ids = [s['id'] for s in songs] or [0]
    ph = ','.join('?'*len(song_ids))
    cur.execute(f"""
        SELECT user, target_id, text
          FROM opinions
         WHERE type='song' AND target_id IN ({ph})
    """, song_ids)
    opinions_map = {sid: [] for sid in song_ids}
    for row in cur.fetchall():
        opinions_map[row['target_id']].append({'user':row['user'], 'text':row['text']})

    # opiniões sobre artistas
    artist_ids = [a['id'] for a in artists] or [0]
    ph = ','.join('?'*len(artist_ids))
    cur.execute(f"""
        SELECT user, target_id, text
          FROM opinions
         WHERE type='artist' AND target_id IN ({ph})
    """, artist_ids)
    artist_opinions_map = {aid: [] for aid in artist_ids}
    for row in cur.fetchall():
        artist_opinions_map[row['target_id']].append({'user':row['user'], 'text':row['text']})

    conn.close()
    return render_template(
        'users/liked.html',
        user=name,
        songs=songs,
        artists=artists,
        liked_items=liked_items,
        opinions_map=opinions_map,
        artist_opinions_map=artist_opinions_map
    )

@app.route('/like', methods=['POST'])
def give_like():
    user      = request.form['user']
    type_     = request.form['type']
    target_id = int(request.form['target_id'])
    value     = int(request.form['value'])
    conn = connect_db(); cur = conn.cursor()
    if value == 1:
        cur.execute("""
            INSERT OR REPLACE INTO likes (user,type,target_id,value)
            VALUES (?, ?, ?, 1)
        """, (user, type_, target_id))
        flash('Curtido!')
    else:
        cur.execute("""
            DELETE FROM likes
             WHERE user=? AND type=? AND target_id=?
        """, (user, type_, target_id))
        flash('Descurtido!')
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('user_dashboard', name=user))


# ========== OPINIONS ==========

@app.route('/opinion/song/<int:song_id>', methods=['POST'])
def opinion_song(song_id):
    user = request.form['user']
    text = request.form['text']
    conn = connect_db(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO opinions (user,type,target_id,text) VALUES (?, 'song', ?, ?)",
        (user, song_id, text)
    )
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('user_dashboard', name=user))

@app.route('/opinion/artist/<int:artist_id>', methods=['POST'])
def opinion_artist(artist_id):
    user = request.form['user']
    text = request.form['text']
    conn = connect_db(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO opinions (user,type,target_id,text) VALUES (?, 'artist', ?, ?)",
        (user, artist_id, text)
    )
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('user_dashboard', name=user))


# ========== SEARCH ==========

@app.route('/search/most_liked')
def most_liked():
    session.pop('last_genres', None)
    user = request.args.get('user','')
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT s.*, a.name AS artist_name,
               COALESCE(SUM(l.value),0) AS total_likes
          FROM songs s
     LEFT JOIN likes l
            ON l.target_id=s.id AND l.type='song'
         JOIN artists a ON s.artist_id = a.id
      GROUP BY s.id
      ORDER BY total_likes DESC
    """)
    songs = cur.fetchall()

    cur.execute("""
        SELECT a.*, COALESCE(SUM(l.value),0) AS total_likes
          FROM artists a
     LEFT JOIN likes l
            ON l.target_id=a.id AND l.type='artist'
      GROUP BY a.id
      ORDER BY total_likes DESC
    """)
    artists = cur.fetchall()

    cur.execute("SELECT type,target_id FROM likes WHERE user=?", (user,))
    liked_items = {(r['type'],r['target_id']) for r in cur.fetchall()}

    # opiniões vazias por padrão
    opinions_map        = {s['id']: [] for s in songs}
    artist_opinions_map = {a['id']: [] for a in artists}

    conn.close()
    return render_template(
        'users/search_most_liked.html',
        songs=songs,
        artists=artists,
        user=user,
        liked_items=liked_items,
        opinions_map=opinions_map,
        artist_opinions_map=artist_opinions_map
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

    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

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

    cur.execute("SELECT type,target_id FROM likes WHERE user=?", (user,))
    liked_items = {(r['type'],r['target_id']) for r in cur.fetchall()}

    opinions_map        = {s['id']: [] for s in songs}
    artist_opinions_map = {a['id']: [] for a in artists}

    conn.close()
    return render_template(
        'users/search_by_genre_result.html',
        songs=songs,
        artists=artists,
        genres=genres,
        user=user,
        liked_items=liked_items,
        opinions_map=opinions_map,
        artist_opinions_map=artist_opinions_map
    )

@app.route('/search/genre/reset')
def reset_genre_search():
    session.pop('last_genres', None)
    return redirect(url_for('search_by_genre'))

@app.route('/search/name', methods=['GET','POST'])
def search_by_name():
    session.pop('last_genres', None)

    if request.method == 'POST':
        termo = request.form['name']; user = request.form['user']
        session['last_search'] = termo; session['last_user'] = user
    else:
        termo = session.get('last_search'); user = session.get('last_user')

    if not termo or not user:
        return render_template('users/search_by_name_form.html')

    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT s.*, a.name AS artist_name
          FROM songs s
          JOIN artists a ON s.artist_id = a.id
         WHERE s.title LIKE ?
    """, ('%'+termo+'%',))
    songs = cur.fetchall()

    cur.execute("SELECT * FROM artists WHERE name LIKE ?", ('%'+termo+'%',))
    artists = cur.fetchall()

    cur.execute("SELECT type,target_id FROM likes WHERE user=?", (user,))
    liked_items = {(r['type'],r['target_id']) for r in cur.fetchall()}

    opinions_map        = {s['id']: [] for s in songs}
    artist_opinions_map = {a['id']: [] for a in artists}

    conn.close()
    return render_template(
        'users/search_by_name_results.html',
        songs=songs,
        artists=artists,
        termo=termo,
        user=user,
        liked_items=liked_items,
        opinions_map=opinions_map,
        artist_opinions_map=artist_opinions_map
    )

if __name__ == '__main__':
    app.run(debug=True)
