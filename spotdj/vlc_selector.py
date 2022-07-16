import time
from pathlib import Path
from typing import List

from spotdj.vlc import Vlc

class VlcSelector:
    def __init__(self, vlc: Vlc):
        self.vlc = vlc

    def choose_from(self, paths: List[Path]) -> int:
        self.vlc.client.clear()
        for path in paths:
            self.vlc.client.enqueue(str(path))

        # keep alive

        while not self.vlc.is_paused():
            time.sleep(0.5)

        chosen = self.vlc.client.info()["data"]["track_number"]
        self.vlc.client.clear()

        return chosen
