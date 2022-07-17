import asyncio
import time
from asyncio import Lock
from pathlib import Path
from typing import List

from spotdj.vlc import Vlc

class VlcSelector:
    def __init__(self, vlc: Vlc):
        self.lock = Lock()
        self.vlc = vlc

    async def choose_from(self, paths: List[Path]) -> int:
        async with self.lock:
            self.vlc.client.clear()
            for path in paths:
                self.vlc.client.enqueue(str(path))

            # keep alive
            while not self.vlc.is_paused():
                await asyncio.sleep(0.5)

            chosen = self.vlc.client.info()["data"]["track_number"]
            self.vlc.client.clear()

            return chosen
