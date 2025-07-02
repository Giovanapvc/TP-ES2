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

CREATE TABLE IF NOT EXISTS opinions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user        TEXT    NOT NULL,                            
  type        TEXT    NOT NULL CHECK(type IN ('song','artist')),
  target_id   INTEGER NOT NULL,
  text        TEXT    NOT NULL,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user)      REFERENCES users(name),
  FOREIGN KEY(target_id) REFERENCES songs(id)      
);