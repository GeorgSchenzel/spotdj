from spotdl.types import Song
import mutagen
from pathlib import Path


def set_metadata(
        path: Path, song: Song
):
    mutagen_file = mutagen.File(path, easy=True)

    mutagen_file["genre"] = "bla"

    mutagen_file.save()