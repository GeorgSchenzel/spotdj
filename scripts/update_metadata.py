from pathlib import Path

from spotdj.spotdj import Spotdj
import asyncio

if __name__ == "__main__":
    with Spotdj(Path.home() / "Music" / "ADL") as spotdj:
        asyncio.run(spotdj.update_metadata())
