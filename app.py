from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'teste123'

def connect_db():
    return sqlite3.connect('data.db')

@app.route('/')
def index():
    return render_template('index.html')

# ========== ARTIST FLOW ==========

@app.route('/artist')
def artist_initial_screen():
    return render_template('/artists/artist_initial_screen.html')

@app.route('/artist/new', methods=['GET', 'POST'])
def create_artist():
    if request.method == 'POST':
        name = request.form['name']
        bio = request.form['bio']
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO artists (name, bio) VALUES (?, ?)", (name, bio))
        conn.commit()
        conn.close()
        return redirect('/artist/login')
    return render_template('/artists/create_artist.html')

@app.route('/artist/login', methods=['GET', 'POST'])
def artist_login():
    if request.method == 'POST':
        name = request.form['name']
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM artists WHERE name = ?", (name,))
        artist = cur.fetchone()
        conn.close()
        if artist:
            session['artist'] = name
            return redirect(url_for('artist_dashboard', name=name))
        else:
            flash("Artista não encontrado")
            
    return render_template('artists/artist_login.html')

@app.route('/artist/<name>')
def artist_dashboard(name):
    return render_template('/artists/artist_dashboard.html', artist=name)

@app.route('/artist/<name>/add', methods=['GET', 'POST'])
def add_song(name):

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    artist = cur.fetchone()

    if not artist:
        return "Artista não encontrado"
    
    artist_id = artist[0]

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        genre = request.form['genre']
        link = request.form['link']
        file_path = request.form['file_path']

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO songs (artist_id, title, description, genre, link, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (artist_id, title, description, genre, link, file_path))
        conn.commit()
        conn.close()

        return redirect(f'/artist/{name}')
    return render_template('/artists/add_song.html', artist=name)

@app.route('/artist/<name>/songs')
def list_songs(name):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    artist = cur.fetchone()

    if not artist:
        conn.close()
        return "Artista não encontrado"
    
    artist_id = artist[0]
    cur.execute("SELECT * FROM songs WHERE artist_id = ?", (artist_id,))
    songs = cur.fetchall()
    conn.close()
    return render_template('/artists/list_songs.html', artist=name, songs=songs)

@app.route('/artist/<name>/edit/<int:id>', methods=['GET', 'POST'])
def edit_songs(name, id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    artist = cur.fetchone()
    if not artist:
        conn.close()
        return "Artista não encontrado", 404
    
    artist_id = artist[0]

    if request.method == 'POST':
        new_title = request.form['title']
        new_description = request.form['description']
        new_genre = request.form['genre']

        cur.execute("""
            UPDATE songs
            SET title = ?, description = ?, genre = ?
            WHERE id = ? AND artist_id = ?
        """, (new_title, new_description, new_genre, id, artist_id))
        conn.commit()
        conn.close()
        return redirect(f'/artist/{name}/songs')
    
    cur.execute("SELECT * FROM songs WHERE id = ? AND artist_id = ?", (id, artist_id))
    song = cur.fetchone()
    conn.close()
    if song:
        return render_template('/artists/edit_songs.html', artist=name, song=song)
    else:
        return "Música não encontrada", 404


# ========== USER FLOW ==========

@app.route('/user')
def user_initial_screen():
    return render_template('users/user_initial_screen.html')

@app.route('/user/new', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        name = request.form['name']
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return redirect('/user/login')
    return render_template('users/create_user.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        name = request.form['name']
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE name = ?", (name,))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user'] = name
            return redirect(url_for('user_dashboard', name=name))
        else:
            flash("Usuário não encontrado")
    
    return render_template('users/user_login.html')

@app.route('/user/<name>')
def user_dashboard(name):
    session.pop('last_genres', None)
    return render_template('users/user_dashboard.html', user=name)

@app.route('/user/<name>/liked')
def all_likes(name):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.id, s.title, a.name
        FROM songs s
        JOIN artists a ON s.artist_id = a.id
        JOIN likes l ON l.target_id = s.id
        WHERE l.user = ? AND l.type = 'song' AND l.value = 1
    """, (name,))
    songs = cur.fetchall()

    cur.execute("""
        SELECT a.id, a.name
        FROM artists a
        JOIN likes l ON l.target_id = a.id
        WHERE l.user = ? AND l.type = 'artist' AND l.value = 1
    """, (name,))
    artists = cur.fetchall()

    conn.close()
    return render_template('users/liked.html', user=name, songs=songs, artists=artists)

@app.route('/like', methods=['POST'])
def give_like():
    user = request.form['user']
    type_ = request.form['type']
    target_id = int(request.form['target_id'])
    value = int(request.form['value'])

    conn = connect_db()
    cur = conn.cursor()

    if value == 1:
        # Curtir ou re-curtir
        cur.execute("""
            INSERT OR REPLACE INTO likes (user, type, target_id, value)
            VALUES (?, ?, ?, ?)
        """, (user, type_, target_id, value))
        flash('Curtido!')
    else:
        # Descurtir: remove o like
        cur.execute("""
            DELETE FROM likes
            WHERE user = ? AND type = ? AND target_id = ?
        """, (user, type_, target_id))
        flash('Descurtido!')

    conn.commit()
    conn.close()

    if 'last_genres' in session:
        genres = session['last_genres']
        return redirect(url_for('search_by_genre', genres=genres))

    ref = request.referrer or url_for('user_dashboard', name=user)
    return redirect(ref)

@app.route('/search/most_liked')
def most_liked():
    session.pop('last_genres', None)
    user = request.args.get('user', '')
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT songs.*, artists.name AS artist_name, 
               COALESCE(SUM(likes.value), 0) AS total_likes
        FROM songs
        LEFT JOIN likes ON songs.id = likes.target_id AND likes.type = 'song'
        JOIN artists ON songs.artist_id = artists.id
        GROUP BY songs.id
        ORDER BY total_likes DESC
    """)
    songs = cur.fetchall()

    cur.execute("""
        SELECT artists.*, COALESCE(SUM(likes.value), 0) AS total_likes
        FROM artists
        LEFT JOIN likes ON artists.id = likes.target_id AND likes.type = 'artist'
        GROUP BY artists.id
        ORDER BY total_likes DESC
    """)
    artists = cur.fetchall()

    cur.execute("SELECT type, target_id FROM likes WHERE user = ?", (user,))
    liked_items = {(row['type'], row['target_id']) for row in cur.fetchall()}

    cur.execute("SELECT type, target_id, value FROM ratings WHERE user = ?", (user,))
    ratings = {(row['type'], row['target_id']): row['value'] for row in cur.fetchall()}

    if 'last_rating' in session:
        last = session['last_rating']
        ratings[(last['type'], last['target_id'])] = last['value']

    conn.close()
    return render_template('users/search_most_liked.html', songs=songs, artists=artists, user=user, liked_items=liked_items, ratings=ratings)

@app.route('/search/genre', methods=['GET', 'POST'])
def search_by_genre():
    user = session.get('user')
    if not user:
        flash("Você precisa estar logado")
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        genres = request.form.getlist('genre')
        if not genres:
            flash("Por favor, selecione ao menos uma opção")
            return render_template('users/search_by_genre_form.html', user=user)

        session['last_genres'] = genres
    else:
        genres = request.args.getlist('genres')
        if not genres:
            return render_template('users/search_by_genre_form.html', user=user)
    
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    placeholders = ','.join(['?'] * len(genres))

    cur.execute(f"""
        SELECT songs.*, artists.name AS artist_name
        FROM songs
        JOIN artists ON songs.artist_id = artists.id
        WHERE songs.genre IN ({placeholders})
    """, genres)
    songs = cur.fetchall()

    cur.execute(f"""
        SELECT DISTINCT artists.* FROM artists
        JOIN songs ON artists.id = songs.artist_id
        WHERE songs.genre IN ({placeholders})
    """, genres)
    artists = cur.fetchall()

    cur.execute("SELECT type, target_id FROM likes WHERE user = ?", (user,))
    liked_items = {(row['type'], row['target_id']) for row in cur.fetchall()}

    cur.execute("SELECT type, target_id, value FROM ratings WHERE user = ?", (user,))
    ratings = {(row['type'], row['target_id']): row['value'] for row in cur.fetchall()}

    if 'last_rating' in session:
        last = session['last_rating']
        ratings[(last['type'], last['target_id'])] = last['value']

    conn.close()
    return render_template('users/search_by_genre_result.html',
                           songs=songs, artists=artists, genres=genres,
                           user=user, liked_items=liked_items, ratings=ratings)

@app.route('/search/genre/reset')
def reset_genre_search():
    session.pop('last_genres', None)
    return redirect(url_for('search_by_genre'))

@app.route('/search/name', methods=['GET', 'POST'])
def search_by_name():
    session.pop('last_genres', None)

    if request.method == 'POST':
        termo = request.form['name']
        user = request.form['user']
        playlist_id = request.form.get('playlist_id')
        session['last_search'] = termo
        session['last_user'] = user
        session['last_playlist_id'] = playlist_id

    else:
        termo = session.get('last_search')
        user = session.get('last_user')
        playlist_id = session.get('last_playlist_id')

    if not termo or not user:
        return render_template('users/search_by_name_form.html')
    
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT songs.*, artists.name AS artist_name
        FROM songs
        JOIN artists on songs.artist_id = artists.id
        WHERE songs.title LIKE ?
    """, ('%' + termo + '%',))
    songs = cur.fetchall()

    if not playlist_id:
        cur.execute("SELECT * FROM artists WHERE name LIKE ?", ('%' + termo + '%',))
        artists = cur.fetchall()
    else:
        artists = []

    cur.execute("SELECT type, target_id FROM likes WHERE user = ?", (user,))
    liked_items = {(row['type'], row['target_id']) for row in cur.fetchall()}

    cur.execute("SELECT type, target_id, value FROM ratings WHERE user = ?", (user,))
    ratings = {(row['type'], row['target_id']): row['value'] for row in cur.fetchall()}

    cur.execute("SELECT song_id FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
    songs_in_playlist = {row['song_id'] for row in cur.fetchall()}

    if 'last_rating' in session:
        last = session['last_rating']
        ratings[(last['type'], last['target_id'])] = last['value']

    conn.close()
    return render_template('users/search_by_name_results.html', songs=songs, artists=artists, termo=termo, user=user, liked_items=liked_items, ratings=ratings, playlist_id=playlist_id, songs_in_playlist=songs_in_playlist)

@app.route('/rate', methods=['POST'])
def give_rating():
    user = request.form['user']
    type_ = request.form['type']
    target_id = int(request.form['target_id'])
    value = int(request.form['value'])

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ratings (user, type, target_id, value)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user, type, target_id) DO UPDATE SET value=excluded.value
    """, (user, type_, target_id, value))
    conn.commit()
    conn.close()

    session['last_rating'] = {
        'user': user,
        'type': type_,
        'target_id': target_id,
        'value': value
    }

    flash('Avaliação registrada!')
    return redirect(request.referrer)

@app.route('/playlists')
def user_playlists():
    user = request.args.get('user')

    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM playlists WHERE user = ?", (user,))
    playlists = cur.fetchall()
    conn.close()

    return render_template('users/playlists.html', playlists=playlists, user=user)

@app.route('/playlist/create', methods=['POST'])
def create_playlist():
    user = request.form['user']
    name = request.form['name']

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO playlists (user, name) VALUES (?, ?)", (user, name))
    conn.commit()
    conn.close()

    flash('Playlist criada!')

    return redirect(request.referrer)

@app.route('/playlist/<int:playlist_id>')
def view_playlist(playlist_id):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
    playlist = cur.fetchone()

    cur.execute("""
        SELECT songs.*, artists.name AS artist_name
        FROM playlist_songs
        JOIN songs ON playlist_songs.song_id = songs.id
        JOIN artists ON songs.artist_id = artists.id
        WHERE playlist_songs.playlist_id = ?
    """, (playlist_id,))
    songs = cur.fetchall()

    cur.execute("SELECT song_id FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
    songs_in_playlist = {row['song_id'] for row in cur.fetchall()}

    conn.close()

    return render_template('users/playlist_detail.html', playlist=playlist, songs=songs, user=playlist['user'], songs_in_playlist=songs_in_playlist)

@app.route('/playlist/<int:playlist_id>/add/<int:song_id>')
def add_song_to_playlist(playlist_id, song_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)", (playlist_id, song_id))
    conn.commit()
    conn.close()

    flash('Música adicionada à playlist!')

    return redirect(request.referrer)

@app.route('/playlist/<int:playlist_id>/remove/<int:song_id>', methods=['POST'])
def remove_song_from_playlist(playlist_id, song_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?", (playlist_id, song_id))
    conn.commit()
    conn.close()

    flash('Música removida da playlist!')

    return redirect(url_for('view_playlist', playlist_id=playlist_id))

@app.route('/user/liked/for_playlist')
def user_liked_for_playlist():
    user = request.args.get('user')
    playlist_id = request.args.get('playlist_id')
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT songs.*, artists.name AS artist_name
        FROM likes
        JOIN songs ON songs.id = likes.target_id
        JOIN artists ON songs.artist_id = artists.id
        WHERE likes.user = ? AND likes.type = 'song' AND likes.value = 1
    """, (user,))
    songs = cur.fetchall()

    cur.execute("SELECT song_id FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
    songs_in_playlist = {row['song_id'] for row in cur.fetchall()}

    conn.close()
    return render_template('users/add_from_liked.html',
                           songs=songs,
                           user=user,
                           playlist_id=playlist_id, songs_in_playlist=songs_in_playlist)

@app.route('/playlist/<int:playlist_id>/delete', methods=['POST'])
def delete_playlist(playlist_id):
    user = request.form['user']
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))

    cur.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
    conn.commit()
    conn.close()

    flash('Playlist removida com sucesso!')
    return redirect(url_for('user_playlists', user=user))


if __name__ == '__main__':
    app.run(debug=True)
