import asyncio
from asyncio import Semaphore, sleep
from concurrent.futures import ThreadPoolExecutor
from typing import List

from spotdl.types import Song
from rymscraper import rymscraper
from rymscraper.utils import get_url_from_artist_name, get_album_infos
from rapidfuzz import fuzz

from spotdj.database import Database, SongEntry
import re

regex_remove_feat = re.compile("\(feat.*?\)")

class MetadataProvider:
    def __init__(self, database: Database, executor: ThreadPoolExecutor):
        self.database = database
        self.network = rymscraper.RymNetwork()
        self.browser = self.network.browser
        self.executor = executor
        self.semaphore = Semaphore(1)

    def fetch_rym_data(self, song):
        try:
            artist_url = get_url_from_artist_name(self.browser, song.artist)
        except TypeError:
            return [], [], [], "not found"

        self.browser.get_url(artist_url)
        soup = self.browser.get_soup()

        artist_discography_list = [
            [x.text.strip(), "https://rateyourmusic.com" + x.find("a")["href"]]
            for x in soup.find_all("div", {"class": "disco_mainline"})
        ]

        singles = list(
            filter(lambda x: x[1].startswith("https://rateyourmusic.com/release/single/"), artist_discography_list))
        albums = list(
            filter(lambda x: x[1].startswith("https://rateyourmusic.com/release/album/"), artist_discography_list))

        genres, descriptors, url = self.fetch_rym_data_from_best_match(singles, song.name)
        album_genres, _, album_url = self.fetch_rym_data_from_best_match(albums, song.album_name) if song.album_name is not None else []

        if url is None:
            url = album_url

        if url is None:
            url = "not found"

        return genres, descriptors, album_genres, url

    def fetch_rym_data_from_best_match(self, discography: List[List[str]], target: str):

        if len(discography) == 0:
            return [], [], None

        def score(a, b):
            ratio = fuzz.ratio(a, b)
            cut_ratio = fuzz.ratio(a, regex_remove_feat.sub("", b))

            return max(ratio, cut_ratio)

        chosen_title, chosen_url = max(discography, key=lambda x: score(x[0], target))
        matching_score = score(chosen_title, target)

        if matching_score < 70:
            return [], [], None

        self.browser.get_url(chosen_url)
        album_infos = get_album_infos(self.browser.get_soup())

        genres = album_infos["Genres"].replace("\n", ",").split(",")
        genres = [g.strip() for g in genres]

        descriptors = album_infos["Descriptors"].replace("\n", ", ").split(", ")
        descriptors = [d.strip() for d in descriptors if d != ""]

        return genres, descriptors, chosen_url

    def update_metadata(self, song: Song, song_entry: SongEntry) -> SongEntry:
        genres, descriptors, album_genres, url = self.fetch_rym_data(song)

        song_entry.rym_url = url
        song_entry.genres = genres
        song_entry.descriptors = descriptors
        song_entry.album_genres = album_genres

        return song_entry

    async def update_metadata_async(self, song: Song, song_entry: SongEntry) -> SongEntry:
        async with self.semaphore:
            song_entry = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.update_metadata, song, song_entry
            )

            # sleep to reduce chance of getting rate limited or even ip banned
            await sleep(5)

            return song_entry
