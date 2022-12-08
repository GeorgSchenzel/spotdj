import json
from dataclasses import dataclass, field
from pathlib import Path
import shutil
from typing import List


@dataclass
class SongEntry:
    song_id: str
    file: Path
    download_url: str
    rym_url: str = None
    genres: List[str] = field(default_factory=list)
    album_genres: List[str] = field(default_factory=list)
    descriptors: List[str] = field(default_factory=list)


@dataclass
class PlaylistEntry:
    playlist_id: str
    m3u_file: Path


@dataclass
class ArtistCacheEntry:
    url: str
    discography: List[List[str]]


class Database:
    def __init__(self, parent: Path):
        self.path = parent / "spotdj.json"
        self.cache_path = parent / "spotdj-cache.json"
        self.data = {"songs": {}, "playlists": {}}
        self.cache_data = {"artists": {}}

        if self.path.exists():
            # make backups you idiot
            shutil.copy(self.path, self.path.with_suffix(".backup"))

            with open(self.path, "r") as openfile:
                self.data = json.load(openfile)

        if self.cache_path.exists():
            with open(self.cache_path, "r") as openfile:
                self.cache_data = json.load(openfile)

    @property
    def songs(self):
        return self.data["songs"]

    @property
    def playlists(self):
        return self.data["playlists"]

    def get_songs(self):
        for song_id, entry in self.songs.items():
            yield SongEntry(song_id,
                            Path(entry.get("filename", "")),
                            entry.get("download_url", ""),
                            entry.get("rym_url"),
                            entry.get("genres", []),
                            entry.get("album_genres", []),
                            entry.get("descriptors", []))

    def get_song(self, song_id: str):
        if song_id not in self.songs:
            return None

        entry = self.songs[song_id]
        return SongEntry(song_id,
                         Path(entry.get("filename", "")),
                         entry.get("download_url", ""),
                         entry.get("rym_url"),
                         entry.get("genres", []),
                         entry.get("album_genres", []),
                         entry.get("descriptors", []))

    def store_song(self, song: SongEntry):
        self.songs[song.song_id] = {
            "filename": str(song.file.name),
            "download_url": song.download_url,
            "rym_url": song.rym_url,
            "genres": song.genres,
            "album_genres": song.album_genres,
            "descriptors": song.descriptors
        }
        self.save()

    def delete_song(self, song_id: str):
        del self.songs[song_id]
        self.save()

    def save(self):
        with open(self.path, "w+") as outfile:
            json.dump(self.data, outfile, indent=2)

    def store_playlist(self, playlist: PlaylistEntry):
        self.playlists[playlist.playlist_id] = {"m3u_file": str(playlist.m3u_file.name)}
        self.save()

    def store_cache(self, artist: str, entry: ArtistCacheEntry):
        if artist in self.cache_data["artists"]:
            return

        self.cache_data["artists"][artist] = {
            "url": entry.url,
            "discography": entry.discography,
        }
        self.save_cache()

    def read_cache(self, artist: str) -> ArtistCacheEntry | None:
        if artist not in self.cache_data["artists"]:
            return None

        entry = self.cache_data["artists"][artist]
        return ArtistCacheEntry(entry["url"], entry["discography"])

    def save_cache(self):
        with open(self.cache_path, "w+") as outfile:
            json.dump(self.cache_data, outfile, indent=2)
