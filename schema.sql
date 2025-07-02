CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    bio TEXT
);

CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id INTEGER,
    title TEXT,
    description TEXT,
    genre TEXT,
    link TEXT,
    file_path TEXT,
    FOREIGN KEY (artist_id) REFERENCES artists(id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS likes (
    user TEXT,
    type TEXT CHECK(type IN ('song', 'artist')),
    target_id INTEGER,
    value INTEGER CHECK(value IN (-1, 1)),
    PRIMARY KEY (user, type, target_id)
);

CREATE TABLE IF NOT EXISTS ratings (
    user TEXT,
    type TEXT CHECK(type IN ('song', 'artist')),
    target_id INTEGER,
    value INTEGER CHECK(value BETWEEN 1 AND 5),
    PRIMARY KEY(user, type, target_id)
);

CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS playlist_songs (
    playlist_id INTEGER,
    song_id INTEGER,
    PRIMARY KEY (playlist_id, song_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);