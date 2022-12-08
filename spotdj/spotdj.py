__version__ = "0.1.0"

import asyncio
import concurrent.futures
import logging
from asyncio import Semaphore
from pathlib import Path

from spotdl import Spotdl, Song
from spotdl.providers.audio import YouTube as SpotDlYoutube
from spotdl.types import Playlist
from spotdl.utils.config import DEFAULT_CONFIG
from spotdl.utils.formatter import create_file_name, create_search_query
from spotdl.utils.metadata import set_id3_mp3

from pytube import YouTube as PyTubeYouTube

from spotdj.converter import Converter
from spotdj.database import Database, SongEntry
from spotdj.downloader import Downloader
from spotdj.metadata_provider import MetadataProvider
from spotdj.playlists import store_playlist
from spotdj.searcher import Searcher
from spotdj.selectors.bestmatch import BestMatch


class Spotdj:
    def __init__(self, location=Path("./spotdj-download"), rym_timeout=5):
        self.location = location
        self.location.mkdir(exist_ok=True)

        self.thread_executor = concurrent.futures.ThreadPoolExecutor()
        self.song_prefetch_semaphore = Semaphore(5)

        self.database = Database(self.location)
        self.metadata_provider = MetadataProvider(self.database, self.thread_executor, timeout=rym_timeout)

        self.spotdl = Spotdl(
            client_id=DEFAULT_CONFIG["client_id"],
            client_secret=DEFAULT_CONFIG["client_secret"],
        )
        self.selector = BestMatch()

        self.searcher = Searcher(
            self.thread_executor, additional_queries=["extended", "club"]
        )
        self.downloader = Downloader(self.location / "tmp", self.thread_executor)
        self.converter = Converter(self.thread_executor)

        self.stopped = False

    def __enter__(self):
        return self

    async def update_metadata(self, timeout=5):
        for song_entry in self.database.get_songs():

            if song_entry.rym_url is not None:
                print("Skipping {}".format(song_entry.file))
                continue

            # use this semaphore to avoid getting rate limited by spotify
            async with self.song_prefetch_semaphore:
                song = await asyncio.get_event_loop().run_in_executor(
                    self.thread_executor, Song.from_url, f"https://open.spotify.com/track/{song_entry.song_id}"
                )

                song_entry = await self.metadata_provider.update_metadata_async(song, song_entry)
                self.database.store_song(song_entry)

                if song_entry.rym_url == "not found":
                    print("Failed {}".format(song.display_name))
                else:
                    print("Success {}".format(song.display_name))

    async def download_playlist(self, playlist_url: str):
        if self.stopped:
            return

        playlist = Playlist.from_url(playlist_url)
        playlist_metadata = Playlist.get_metadata(playlist_url)

        print("Downloading Playlist {}".format(playlist_metadata["name"]))

        tasks = []
        for song in playlist.songs:
            song_entry = self.database.get_song(song.song_id)
            if song_entry is not None:
                if self.location.joinpath(song_entry.file).exists():
                    print("Skipping {}".format(song.display_name))
                    continue
                else:
                    self.database.delete_song(song.song_id)

            tasks.append(self.download_song(song))

        await asyncio.gather(*tasks)

        store_playlist(
            self.database,
            playlist,
            self.location / Path("{}.m3u".format(playlist_metadata["name"])),
        )
        print("Stored Playlist {}".format(playlist_metadata["name"]))

    async def download_song(self, song: Song):
        try:
            async with self.song_prefetch_semaphore:
                if self.stopped:
                    return

                # use spotdl for searching and selecting the best result
                url = SpotDlYoutube().search(song)

                # use pytube to download the song
                yt = PyTubeYouTube(url)
                tmp_path = await self.downloader.download_search_result_async(yt)
                print("Downloaded {}".format(song.display_name))

                download_filename = create_file_name(
                    song, "{artists} - {title}.{output-ext}", "mp3"
                )
                download_filename = self.location / download_filename

                await self.converter.to_mp3_async(tmp_path, download_filename)
                print("Converted {}".format(song.display_name))

                # store the spotify song id as a comment
                song.download_url = song.song_id

                # first get basic info from spotify song object
                set_id3_mp3(download_filename, song)

                song_entry = SongEntry(song.song_id, download_filename, yt.watch_url)

                # then override with our own logic
                song_entry = self.metadata_provider.update_metadata(song, song_entry)

                self.database.store_song(song_entry)
                print("Stored {}".format(song.display_name))

        except Exception as e:
            print(
                "\nEncountered an exception while downloading {}".format(
                    song.display_name
                )
            )
            logging.exception(e)
            print("Stopping\n")
            self.stopped = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.downloader.cleanup()
