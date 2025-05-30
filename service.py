from typing import Dict, List, Optional
from entities import Artist, Song, GENRES
import repo

# ---------- Helpers ----------
def _name_exists(store: Dict[str, Artist], name: str) -> bool:
    return any(a.name.lower() == name.lower() for a in store.values())

def _find_song(store: Dict[str, Artist], artist_id: str, song_id: str) -> Song:
    for s in store[artist_id].songs:
        if s.id == song_id:
            return s
    raise KeyError("Song not found")

# ---------- Artist ----------
def add_artist(store: Dict[str, Artist], name: str, bio: str = "") -> Artist:
    if _name_exists(store, name):
        raise ValueError("Nome de artista já existe")
    artist = Artist(name=name.strip(), bio=bio.strip())
    store[artist.id] = artist
    repo.save(store)
    return artist

def find_artist_by_name(store: Dict[str, Artist], name: str) -> Optional[Artist]:
    for a in store.values():
        if a.name.lower() == name.lower():
            return a
    return None

def like_artist(store: Dict[str, Artist], artist_id: str):
    store[artist_id].likes += 1
    repo.save(store)

# ---------- Song ----------
def add_song(store: Dict[str, Artist], artist_id: str, *, title: str, description: str,
             genre: str, link: str = "", file_path: str = "") -> Song:
    if genre.lower() not in GENRES:
        raise ValueError("Invalid genre")
    song = Song(title=title.strip(), description=description.strip(),
                genre=genre.lower(), link=link.strip(), file_path=file_path.strip())
    store[artist_id].songs.append(song)
    repo.save(store)
    return song

def edit_song(store: Dict[str, Artist], artist_id: str, song_id: str, **updates):
    song = _find_song(store, artist_id, song_id)
    if 'genre' in updates and updates['genre']:
        g = updates['genre'].lower()
        if g not in GENRES:
            raise ValueError("Invalid genre")
        updates['genre'] = g
    for k, v in updates.items():
        if v is not None:
            setattr(song, k, v.strip() if isinstance(v, str) else v)
    repo.save(store)

# ---------- Likes & Opinions ----------
def like_song(store: Dict[str, Artist], artist_id: str, song_id: str):
    song = _find_song(store, artist_id, song_id)
    song.likes += 1
    repo.save(store)

def add_opinion(store: Dict[str, Artist], artist_id: str, song_id: str, text: str):
    song = _find_song(store, artist_id, song_id)
    song.opinions.append(text.strip())
    repo.save(store)

# ---------- Queries ----------
def songs_by_genre_sorted(store: Dict[str, Artist], genre: str) -> List[Song]:
    return sorted([s for a in store.values() for s in a.songs if s.genre == genre.lower()],
                  key=lambda s: s.likes, reverse=True)

def artists_sorted(store: Dict[str, Artist]) -> List[Artist]:
    return sorted(store.values(), key=lambda a: a.likes, reverse=True)

def find_song_by_name(store: Dict[str, Artist], name: str) -> Optional[Song]:
    name_lc = name.lower().strip()
    for a in store.values():
        for s in a.songs:
            if s.title.lower() == name_lc:
                return s
    return None