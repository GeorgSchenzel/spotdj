import asyncio
from asyncio import Lock
from pathlib import Path
from typing import List

from spotdl import Song

from spotdj.vlc import Vlc

class VlcSelector:
    def __init__(self, vlc: Vlc):
        self.lock = Lock()
        self.vlc = vlc

    async def choose_from(self, song: Song, paths: List[Path]) -> int:
        try:
            async with self.lock:
                print("Choose {}".format(song.display_name))
                self.vlc.client.clear()
                for path in paths:
                    self.vlc.client.enqueue(str(path))

                # keep alive
                while not self.vlc.is_paused():
                    await asyncio.sleep(0.5)

                chosen = self.vlc.client.info()["data"]["track_number"]
                self.vlc.client.clear()

                return chosen
        except ConnectionAbortedError:
            return -1
