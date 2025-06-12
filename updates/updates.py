@app.route('/user/<name>/opinions')
def user_opinions(name):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.type, o.target_id, o.text,
        CASE o.type WHEN 'song' THEN (SELECT title FROM songs WHERE id = o.target_id)
                    WHEN 'artist' THEN (SELECT name FROM artists WHERE id = o.target_id)
        END AS nome
        FROM opinions o
        WHERE o.user = ? 
    """, (name,))
    opinions = cur.fetchall()
    conn.close()
    return render_template('users/opinions.html', user=name, opinions=opinions)


@app.route('/opinion', methods=['POST'])
def give_opinion():
    user = request.form['user']
    type_ = request.form['type']
    target_id = int(request.form['target_id'])
    text = request.form['text']

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO opinions (user, type, target_id, text)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user, type, target_id) DO UPDATE SET text=excluded.text
    """, (user, type_, target_id, text))
    conn.commit()
    conn.close()

    flash('Opinião enviada!')
    return redirect(request.referrer)

@app.route('/artist/<name>/stats', methods=['GET', 'POST'])
def artist_stats(name):

    if session.get('artist') != name:
        return redirect(url_for('artist_login'))


    artist = session.get('artist')
    if not artist:
        flash("Você precisa estar logado como artista.")
        return redirect(url_for('artist_login'))

    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Recupera ID do artista
    cur.execute("SELECT id FROM artists WHERE name = ?", (artist,))
    artist_row = cur.fetchone()
    if not artist_row:
        flash("Artista não encontrado.")
        return redirect(url_for('artist_dashboard'))

    artist_id = artist_row['id']

    # Total de likes nas músicas do artista
    cur.execute("""
        SELECT COUNT(*) AS total_likes
        FROM likes
        JOIN songs ON likes.target_id = songs.id
        WHERE likes.type = 'song' AND songs.artist_id = ?
    """, (artist_id,))
    total_likes = cur.fetchone()['total_likes']

    # Total de opiniões nas músicas do artista
    cur.execute("""
        SELECT COUNT(*) AS total_opinions
        FROM opinions
        JOIN songs ON opinions.target_id = songs.id
        WHERE opinions.type = 'song' AND songs.artist_id = ?
    """, (artist_id,))
    total_opinions = cur.fetchone()['total_opinions']

    conn.close()

    return render_template('artists/stats.html', artist=artist, total_likes=total_likes, total_opinions=total_opinions)



CREATE TABLE IF NOT EXISTS opinions (
    user TEXT,
    type TEXT CHECK(type IN ('song', 'artist')),
    target_id INTEGER,
    text TEXT,
    PRIMARY KEY (user, type, target_id)
);