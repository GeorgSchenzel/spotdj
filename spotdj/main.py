import asyncio
import concurrent.futures
import json
from asyncio import Semaphore
from pathlib import Path
from typing import List

from pytube import Search, YouTube
from spotdl import Spotdl, Song
from spotdl.types import Playlist
from spotdl.utils.config import DEFAULT_CONFIG
from spotdl.utils.formatter import create_file_name, create_search_query

from spotdj.converter import Converter
from spotdj.downloader import Downloader
from spotdj.vlc import Vlc
from spotdj.vlc_selector import VlcSelector



class Spotdj:
    def __init__(self):
        self.thread_executor = concurrent.futures.ThreadPoolExecutor()
        self.song_prefetch_semaphore = Semaphore(3)

        self.spotdl = Spotdl(client_id=DEFAULT_CONFIG["client_id"], client_secret=DEFAULT_CONFIG["client_secret"])

        self.vlc = Vlc()
        self.vlc_selector = VlcSelector(self.vlc)

        self.converter = Converter(self.thread_executor)
        self.downloader = Downloader(Path("./tmp"), self.thread_executor)

        self.database = {}
        self.database_path = Path("./spotdj.json")
        if self.database_path.exists():
            with open(self.database_path, "r") as openfile:
                self.database = json.load(openfile)

    def __enter__(self):
        return self

    async def download_playlist(self, playlist_url: str):
        playlist = Playlist.from_url(playlist_url)

        tasks = []
        for song in playlist.songs:
            if song.song_id in self.database:
                filename = Path(self.database[song.song_id]["filename"])
                if filename.exists():
                    print("Skipping {}".format(song.display_name))
                    continue
                else:
                    del self.database[song.song_id]

            tasks.append(self.download_song(song))

        await asyncio.gather(*tasks)

    def search(self, query: str) -> List[YouTube]:
        results = Search(query).results[:5]
        for yt in results:
            _ = yt.vid_info
        return results

    async def search_async(self, query: str) -> List[YouTube]:
        return await asyncio.get_event_loop().run_in_executor(self.thread_executor, self.search, query)

    async def download_song(self, song: Song):
        async with self.song_prefetch_semaphore:
            results = await self.search_async(create_search_query(song, "{artist} - {title}", False))
            results = self.filter_results(results)

            paths = await self.downloader.download_async(results[:5])
            chosen = await self.vlc_selector.choose_from(song, paths)

            filename = create_file_name(song, "{artists} - {title}.{output-ext}", "mp3")

            await self.converter.to_mp3_async(paths[chosen], filename)

            for path in paths:
                path.unlink()

            self.database[song.song_id] = {"filename": str(filename), "url": results[chosen].watch_url}
            with open(self.database_path, "w+") as outfile:
                json.dump(self.database, outfile)

    @staticmethod
    def filter_results(results: List[YouTube]) -> List[YouTube]:
        def allow(yt: YouTube):
            if yt.length > 60 * 15:
                return False

            return True

        return [r for r in results if allow(r)]

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.vlc.stop()
        except ConnectionAbortedError:
            pass

        self.downloader.cleanup()


playlist_url = "https://open.spotify.com/playlist/08sR2Q2jOLwgo7SylDtZIq?si=50c22033a8624e9e"

with Spotdj() as spotdj:
    asyncio.run(spotdj.download_playlist(playlist_url))
