from entities import Song, Artist

def test_song_fields():
    s = Song("Track", "Someone", 123)
    assert s.title == "Track"
    assert "track" in str(s).lower()

def test_artist_fields():
    a = Artist("Nome", bio="...")
    assert a.name == "Nome"

def test_song_equality_simple():
    a = Song("X", "Y", 1)
    b = Song("X", "Y", 1)
    assert a == b
