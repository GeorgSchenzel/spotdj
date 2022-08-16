import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep
from typing import List, Optional

import mutagen
import requests
from mutagen import MutagenError
from mutagen.mp4 import MP4Cover
from pytube import YouTube, StreamQuery, Stream
from pytube.exceptions import LiveStreamError


def human_format(num) -> str:
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


class Downloader:

    def __init__(self, location: Path, executor: ThreadPoolExecutor):
        self.location = location
        self.threads = 5
        self.executor = executor
        self.paths = [] # type: List[Path]

    def set_metadata(self, path: str, yt: YouTube, result_number: int, audio_stream: Stream):
        mutagen_file = mutagen.File(path, easy=True)
        mutagen_file["artist"] = yt.author
        mutagen_file["tracknumber"] = str(result_number)
        mutagen_file["description"] = "Bitrate: {}, Views: {}".format(audio_stream.abr, human_format(yt.views))
        mutagen_file.save()

        sleep(1)

        thumbnail_data = requests.get(yt.thumbnail_url).content
        mutagen_file = mutagen.File(path)
        mutagen_file["covr"] = [MP4Cover(thumbnail_data)]
        mutagen_file.save()

    def download_search_result(self, result_number: int, yt: YouTube) -> Optional[Path]:
        try:
            streams = StreamQuery(yt.fmt_streams)

            audio_stream = streams.get_audio_only()
            path = audio_stream.download(output_path=str(self.location), filename_prefix="{} ".format(result_number))
        except KeyError:
            return None
        except LiveStreamError:
            return None

        # wait for the previous operation to be completed
        sleep(0.2)

        try:
            self.set_metadata(path, yt, result_number, audio_stream)
        except MutagenError:
            sleep(4)
            self.set_metadata(path, yt, result_number, audio_stream)

        return Path(path)

    async def download_search_result_async(self, result_number: int, yt: YouTube) -> Path:
        path = await asyncio.get_event_loop().run_in_executor(self.executor, self.download_search_result, result_number, yt)
        self.paths.append(path)

        return path

    async def download_async(self, yts: List[YouTube]) -> List[Path]:
        tasks = []
        for i, yt in enumerate(yts):
            tasks.append(self.download_search_result_async(i, yt))

        res: List[Path] = list(await asyncio.gather(*tasks))
        return [x for x in res if x is not None]

    def cleanup(self):
        for path in self.paths:
            if path.exists():
                path.unlink()
