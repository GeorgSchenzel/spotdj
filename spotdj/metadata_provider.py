import asyncio
from asyncio import Semaphore, sleep
from concurrent.futures import ThreadPoolExecutor
from typing import List

from spotdl.types import Song
from rymscraper import rymscraper
from rymscraper.utils import get_url_from_artist_name, get_album_infos
from rapidfuzz import fuzz

from spotdj.database import Database, SongEntry, ArtistCacheEntry
import re
from colorama import Fore
from colorama import Style


regex_remove_feat = re.compile("\(feat.*?\)")


class MetadataProvider:
    def __init__(self, database: Database, executor: ThreadPoolExecutor, timeout=5):
        self.database = database
        self.network = rymscraper.RymNetwork()
        self.browser = self.network.browser
        self.executor = executor
        self.semaphore = Semaphore(1)
        self.timeout = timeout

    def fetch_artist_url_from_artist_name(self, artist):
        cached = self.database.read_cache(artist)
        if cached is not None:
            print(f"{Fore.LIGHTBLACK_EX}  used cached url{Style.RESET_ALL}")
            return cached.url

        try:
            return get_url_from_artist_name(self.browser, artist)
        except TypeError:
            return None

    def fetch_artist_discography(self, artist, artist_url):
        def split_discography(discography):
            singles = list(
                filter(lambda x: x[1].startswith("https://rateyourmusic.com/release/single/"), discography))
            albums = list(
                filter(lambda x: x[1].startswith("https://rateyourmusic.com/release/album/"), discography))

            return singles, albums

        cached = self.database.read_cache(artist)
        if cached is not None:
            print(f"{Fore.LIGHTBLACK_EX}  used cached disco{Style.RESET_ALL}")
            return split_discography(cached.discography)

        self.browser.get_url(artist_url)
        soup = self.browser.get_soup()

        artist_discography_list = [
            [x.text.strip(), "https://rateyourmusic.com" + x.find("a")["href"]]
            for x in soup.find_all("div", {"class": "disco_mainline"})
        ]

        return split_discography(artist_discography_list)

    def cache_data(self, artist, url, discography):
        cached = self.database.read_cache(artist)
        if cached is not None:
            return

        self.database.store_cache(artist, ArtistCacheEntry(url, discography))

    def fetch_rym_data(self, song):
        artist_url = self.fetch_artist_url_from_artist_name(song.artist)
        if artist_url is None:
            return [], [], [], "not found"

        singles, albums = self.fetch_artist_discography(song.artist, artist_url)

        genres, descriptors, url = self.fetch_rym_data_from_best_match(singles, song.name)
        album_genres, _, album_url = self.fetch_rym_data_from_best_match(albums, song.album_name) if song.album_name is not None else []

        if url is None:
            url = album_url

        if url is None:
            url = "not found"

        self.cache_data(song.artist, artist_url, singles + albums)

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

            if song_entry.rym_url == "not found":
                print(f"{Fore.RED}Failed {song.display_name}{Fore.LIGHTBLACK_EX}, now sleeping{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}Success {song.display_name}{Fore.LIGHTBLACK_EX}, now sleeping{Style.RESET_ALL}")

            # sleep to reduce chance of getting rate limited or even ip banned
            await sleep(self.timeout)

            return song_entry
