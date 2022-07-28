import json
from dataclasses import dataclass
from pathlib import Path

from spotdl.types import Playlist


@dataclass
class SongEntry:
    song_id: str
    file: Path
    download_url: str


@dataclass
class PlaylistEntry:
    playlist_id: str
    m3u_file: Path


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

    @property
    def playlists(self):
        return self.data["playlists"]

    def get_song(self, song_id: str):
        if song_id not in self.songs:
            return None

        entry = self.songs[song_id]
        return SongEntry(song_id, Path(entry["filename"]), entry["download_url"])

    def store_song(self, song: SongEntry):
        self.songs[song.song_id] = {"filename": str(song.file), "download_url": song.download_url}
        self.save()

    def delete_song(self, song_id: str):
        del self.songs[song_id]
        self.save()

    def save(self):
        with open(self.path, "w+") as outfile:
            json.dump(self.data, outfile, indent=2)

    def store_playlist(self, playlist: PlaylistEntry):
        self.playlists[playlist.playlist_id] = {"m3u_file": str(playlist.m3u_file)}
        self.save()
