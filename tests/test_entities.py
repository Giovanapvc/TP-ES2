import pytest
from entities import Song

def test_entities__song_attrs_and_str():
    song = Song(title="A", artist="B", duration=180)
    assert song.title == "A"
    assert "A" in str(song)

def test_entities__song_serialization_roundtrip(tmp_path):
    song = Song("X","Y",200)
    path = tmp_path / "s.json"
    song.to_json(path)
    loaded = Song.from_json(path)
    assert loaded == song

def test_entities__invalid_duration_raises():
    with pytest.raises(ValueError):
        Song("T","U",-5)
