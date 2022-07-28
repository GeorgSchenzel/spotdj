import asyncio
import concurrent.futures
from asyncio import Semaphore
from pathlib import Path

from spotdl import Spotdl, Song
from spotdl.types import Playlist
from spotdl.utils.config import DEFAULT_CONFIG
from spotdl.utils.formatter import create_file_name, create_search_query
from spotdl.utils.metadata import set_id3_mp3

from spotdj.converter import Converter
from spotdj.database import Database, SongEntry
from spotdj.downloader import Downloader
from spotdj.name_selector import NameSelector
from spotdj.playlists import store_playlist
from spotdj.searcher import Searcher
from spotdj.vlc import Vlc
from spotdj.vlc_selector import VlcSelector



class Spotdj:
    def __init__(self):
        self.thread_executor = concurrent.futures.ThreadPoolExecutor()
        self.song_prefetch_semaphore = Semaphore(3)

        self.database = Database(Path("./spotdj.json"))

        self.spotdl = Spotdl(client_id=DEFAULT_CONFIG["client_id"], client_secret=DEFAULT_CONFIG["client_secret"])
        self.vlc = Vlc()
        self.vlc_selector = VlcSelector(self.vlc)
        self.name_selector = NameSelector()

        self.searcher = Searcher(self.thread_executor, additional_queries=["extended", "club"])
        self.downloader = Downloader(Path("./tmp"), self.thread_executor)
        self.converter = Converter(self.thread_executor)

    def __enter__(self):
        return self

    async def download_playlist(self, playlist_url: str):
        playlist = Playlist.from_url(playlist_url)
        playlist_metadata = Playlist.get_metadata(playlist_url)

        tasks = []
        for song in playlist.songs:
            song_entry = self.database.get_song(song.song_id)
            if song_entry is not None:
                if song_entry.file.exists():
                    print("Skipping {}".format(song.display_name))
                    continue
                else:
                    self.database.delete_song(song.song_id)

            tasks.append(self.download_song(song))

        await asyncio.gather(*tasks)

        store_playlist(self.database, playlist, Path("{}.m3u".format(playlist_metadata["name"])))

    async def download_song(self, song: Song):
        async with self.song_prefetch_semaphore:
            results = await self.searcher.search_async(create_search_query(song, "{artist} - {title}", False))
            paths = await self.downloader.download_async(results)
            chosen = await self.vlc_selector.choose_from(song, paths)
            if chosen == -1:
                self.name_selector.cancel()
                return

            filename = create_file_name(song, "{artists} - {title}.{output-ext}", "mp3")
            filename = await self.name_selector.select(filename, paths[chosen])

            await self.converter.to_mp3_async(paths[chosen], filename)

            # store the spotify song id as a comment
            song.download_url = song.song_id
            set_id3_mp3(filename, song)

            for path in paths:
                path.unlink()

            self.database.store_song(SongEntry(song.song_id, filename, results[chosen].watch_url))
            print("Stored {}".format(song.display_name))

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.vlc.stop()
        except ConnectionAbortedError:
            pass

        self.downloader.cleanup()


playlist_url = "https://open.spotify.com/playlist/6ZSUmnKZO8RqQMaxNq6cZf?si=bcd3206b488e489b"

with Spotdj() as spotdj:
    asyncio.run(spotdj.download_playlist(playlist_url))
