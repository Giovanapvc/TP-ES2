"""SQLite persistence layer."""
import sqlite3
from pathlib import Path
from typing import Dict
from entities import Artist, Song

DB_FILE = Path(__file__).with_name("data.db")

def _conn():
    return sqlite3.connect(DB_FILE)

def _init():
    conn = _conn()
    cur = conn.cursor()
    # unique constraint on artist name
    cur.execute("CREATE TABLE IF NOT EXISTS artists(id TEXT PRIMARY KEY,name TEXT UNIQUE,bio TEXT,likes INTEGER)")
    cur.execute("""CREATE TABLE IF NOT EXISTS songs(
        id TEXT PRIMARY KEY,
        artist_id TEXT,
        title TEXT,
        description TEXT,
        genre TEXT,
        link TEXT,
        file_path TEXT,
        likes INTEGER,
        FOREIGN KEY(artist_id) REFERENCES artists(id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS opinions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        song_id TEXT,
        text TEXT,
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )""")
    conn.commit()
    conn.close()

_init()

def load() -> Dict[str, Artist]:
    conn = _conn()
    cur = conn.cursor()
    artists: Dict[str, Artist] = {}
    for id_, name, bio, likes in cur.execute("SELECT id,name,bio,likes FROM artists"):
        artists[id_] = Artist(name=name, bio=bio, id=id_, likes=likes)
    for row in cur.execute("SELECT id,artist_id,title,description,genre,link,file_path,likes FROM songs"):
        sid, aid, title, desc, genre, link, file_path, likes = row
        song = Song(title=title, description=desc, genre=genre, link=link,
                    file_path=file_path, id=sid, likes=likes)
        artists[aid].songs.append(song)
    for song_id, text in cur.execute("SELECT song_id,text FROM opinions ORDER BY id"):
        for art in artists.values():
            for s in art.songs:
                if s.id == song_id:
                    s.opinions.append(text)
                    break
    conn.close()
    return artists

def save(store: Dict[str, Artist]):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM artists")
    cur.execute("DELETE FROM songs")
    cur.execute("DELETE FROM opinions")
    for art in store.values():
        cur.execute("INSERT INTO artists(id,name,bio,likes) VALUES (?,?,?,?)",
                    (art.id, art.name, art.bio, art.likes))
        for s in art.songs:
            cur.execute("""INSERT INTO songs
                (id,artist_id,title,description,genre,link,file_path,likes)
                VALUES (?,?,?,?,?,?,?,?)""",
                (s.id, art.id, s.title, s.description, s.genre,
                 s.link, s.file_path, s.likes))
            for op in s.opinions:
                cur.execute("INSERT INTO opinions(song_id,text) VALUES (?,?)",
                            (s.id, op))
    conn.commit()
    conn.close()