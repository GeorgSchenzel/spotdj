from pathlib import Path
from typing import List

from pytube import Search, YouTube
from spotdl import Spotdl
from spotdl.types import Playlist
from spotdl.utils.config import DEFAULT_CONFIG
from spotdl.utils.formatter import create_file_name, create_search_query

from spotdj.converter import Converter
from spotdj.downloader import Downloader
from spotdj.vlc import Vlc
from spotdj.vlc_selector import VlcSelector


def filter_results(results: List[YouTube]) -> List[YouTube]:
    def allow(yt: YouTube):
        if yt.length > 60 * 15:
            return False

        return True

    return [r for r in results if allow(r)]


spotdl = Spotdl(client_id=DEFAULT_CONFIG["client_id"], client_secret=DEFAULT_CONFIG["client_secret"])
vlc = Vlc()
vlc_selector = VlcSelector(vlc)
converter = Converter()

downloader = Downloader(Path("./tmp"))

playlist_url = "https://open.spotify.com/playlist/08sR2Q2jOLwgo7SylDtZIq?si=50c22033a8624e9e"
playlist = Playlist.from_url(playlist_url)

for song in playlist.songs:
    filename = create_file_name(song, "{artists} - {title}.{output-ext}", "mp3")
    if filename.exists():
        print("Skipping {}".format(song.display_name))
        continue

    results = Search(create_search_query(song, "{artist} - {title}", False)).results
    results = filter_results(results)

    paths = downloader.download(results[:5])
    chosen = vlc_selector.choose_from(paths)
    converter.to_mp3(paths[chosen], filename)

    for path in paths:
        path.unlink()

vlc.stop()
