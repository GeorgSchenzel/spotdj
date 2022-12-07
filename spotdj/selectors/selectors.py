from pathlib import Path
from typing import List
from spotdl import Song
from pytube import YouTube


class Selector:
    async def choose_from(self, song: Song, paths: List[YouTube]) -> int:
        pass
