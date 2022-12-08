from pathlib import Path

from spotdj.spotdj import Spotdj
import asyncio

playlist_url = "https://open.spotify.com/playlist/4N2z4bAv5KOYdCzB6cM9zL?si=a169d3a38811401e"

if __name__ == "__main__":
    with Spotdj(rym_timeout=1) as spotdj:
        #asyncio.run(spotdj.download_playlist(playlist_url))
        asyncio.run(spotdj.update_metadata())
