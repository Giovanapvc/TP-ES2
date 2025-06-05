from dataclasses import dataclass, field
from typing import List
import uuid

GENRES = [
    "rock", "pop", "jazz", "hip-hop", "blues", "metal",
    "classical", "electronic", "folk", "other",
]

def _new_id() -> str:
    return uuid.uuid4().hex[:8]

@dataclass
class Song:
    title: str
    description: str
    genre: str
    link: str = ""
    file_path: str = ""
    id: str = field(default_factory=_new_id)
    likes: int = 0
    opinions: List[str] = field(default_factory=list)

@dataclass
class Artist:
    name: str
    bio: str = ""
    id: str = field(default_factory=_new_id)
    songs: List[Song] = field(default_factory=list)
    likes: int = 0
    opinions: List[str] = field(default_factory=list)