import slugify as slugify

from spotdj.selectors.selectors import Selector
from pathlib import Path
from typing import List, Dict, Tuple
from spotdl import Song
from rapidfuzz import fuzz
from slugify import slugify
from spotdl.utils.formatter import create_song_title, create_search_query
from pytube import YouTube


class BestMatch(Selector):
    async def choose_from(self, song: Song, results: List[YouTube]) -> int:
        pass

