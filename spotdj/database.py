import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SongEntry:
    song_id: str
    filename: Path
    download_url: str


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.data = {
            "songs": {},
            "playlists": {}
        }

        if self.path.exists():
            with open(self.path, "r") as openfile:
                self.data = json.load(openfile)

    @property
    def songs(self):
        return self.data["songs"]

    def get_song(self, song_id: str):
        if song_id not in self.songs:
            return None

        entry = self.songs[song_id]
        return SongEntry(song_id, Path(entry["filename"]), entry["download_url"])

    def store_song(self, song: SongEntry):
        self.songs[song.song_id] = {"filename": str(song.filename), "download_url": song.download_url}
        self.save()

    def delete_song(self, song_id: str):
        del self.songs[song_id]
        self.save()

    def save(self):
        with open(self.path, "w+") as outfile:
            json.dump(self.data, outfile)
