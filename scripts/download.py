from pathlib import Path

from spotdj import Spotdj
import asyncio

playlists = [
    "https://open.spotify.com/playlist/3085jZ72W4oQZzYJNIwJrz?si=4377f3685e6440fe", # x No Idea
    "https://open.spotify.com/playlist/760SUlqZQkhBGrD3Y7HIee?si=2e9e6c4f75814bac", # x Future Rave
    "https://open.spotify.com/playlist/5zg9mkiTRhZgxoEScfJDRB?si=5daa5b11df2f487d", # x Remixes of classics
    "https://open.spotify.com/playlist/20463owQuVHYpZ9YCjvN5y?si=eee127959f164206", # x No Idea but harder
    "https://open.spotify.com/playlist/7Hon4ajsRU1RFqSXra076p?si=d042d9de008343f4", # x No Idea but chillier
    "https://open.spotify.com/playlist/6e0UTtlUkK8Ca2Y2jXpuRQ?si=4ef1cd965e3c4c18", # x UK Garage
    "https://open.spotify.com/playlist/74FvbKVTJuSfuDtp4TLpyT?si=4031980cb2d74ed2", # x Techno
    "https://open.spotify.com/playlist/6YGvX2GugYcoyDxJxZTJBn?si=3230467530df4c58", # x Techhouse
    "https://open.spotify.com/playlist/08sR2Q2jOLwgo7SylDtZIq?si=ea5fc5725b6846b8", # x Top Baselines
    "https://open.spotify.com/playlist/4rTYfmoF3x3XdOFzRsDPk1?si=64993d71da704498", # x House
    "https://open.spotify.com/playlist/1Wo03rxGc6S9htYCUxremd?si=a6b4b47c87464357", # x This Melody
]


async def main():
    with Spotdj(Path.home() / "Music") as spotdj:
        for playlist in playlists:
            await spotdj.download_playlist(playlist)


if __name__ == "__main__":
    asyncio.run(main())
