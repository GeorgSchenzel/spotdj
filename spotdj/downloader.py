import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

import mutagen
import requests
from mutagen.mp4 import MP4Cover
from pytube import YouTube, StreamQuery


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

    def download_search_result(self, result_number: int, yt: YouTube) -> Path:
        print("Downloading {} {}".format(result_number, yt.title))
        streams = StreamQuery(yt.fmt_streams)
        audio_stream = streams.get_audio_only()
        path = audio_stream.download(output_path=str(self.location), filename_prefix="{} ".format(result_number))

        mutagen_file = mutagen.File(path, easy=True)
        mutagen_file["artist"] = yt.author
        mutagen_file["tracknumber"] = str(result_number)
        mutagen_file["description"] = "Bitrate: {}, Views: {}".format(audio_stream.abr, human_format(yt.views))
        mutagen_file.save()

        thumbnail_data = requests.get(yt.thumbnail_url).content
        mutagen_file = mutagen.File(path)
        mutagen_file["covr"] = [MP4Cover(thumbnail_data)]
        mutagen_file.save()

        return Path(path)

    async def download_search_result_async(self, result_number: int, yt: YouTube) -> Path:
        return await asyncio.get_event_loop().run_in_executor(self.executor, self.download_search_result, result_number, yt)

    async def download_async(self, yts: List[YouTube]) -> List[Path]:
        tasks = []
        for i, yt in enumerate(yts):
            tasks.append(self.download_search_result_async(i, yt))

        print("gather download")
        return list(await asyncio.gather(*tasks))
