from pathlib import Path
from typing import List

import spotdl.types
from spotdl import Song
from spotdl.types import Playlist
from spotipy import Spotify

from spotdj.database import Database, PlaylistEntry


def create_m3u_content(database: Database, song_list: List[Song]) -> str:
    """
    Create m3u content and return it as a string.

    ### Arguments
    - song_list: the list of songs
    - template: the template to use
    - file_extension: the file extension to use
    - short: whether to use the short version of the template

    ### Returns
    - the m3u content as a string
    """

    text = ""
    for song in song_list:
        text += str(database.get_song(song.song_id).file) + "\n"

    return text


def store_playlist(database: Database, playlist: Playlist, file: Path):
    m3u_content = create_m3u_content(database, playlist.songs)

    with open(file, "w+", encoding="utf-8") as m3u_file:
        m3u_file.write(m3u_content)

    # noinspection PyProtectedMember
    playlist_id = Spotify._get_id(None, "playlist", playlist.url)
    database.store_playlist(PlaylistEntry(playlist_id, file))
