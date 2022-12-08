import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep
from typing import List, Optional

from pytube import YouTube, StreamQuery, Stream
from pytube.exceptions import LiveStreamError


def human_format(num) -> str:
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return "%.2f%s" % (num, ["", "K", "M", "G", "T", "P"][magnitude])


class Downloader:
    def __init__(self, location: Path, executor: ThreadPoolExecutor):
        self.location = location
        self.threads = 5
        self.executor = executor
        self.paths = []  # type: List[Path]

    def download_search_result(self, result_number: int, yt: YouTube) -> Optional[Path]:
        try:
            streams = StreamQuery(yt.fmt_streams)

            audio_stream = streams.get_audio_only()
            if audio_stream is None:
                return None

            path = audio_stream.download(
                output_path=str(self.location),
            )
        except KeyError:
            return None
        except LiveStreamError:
            return None

        # wait for the previous operation to be completed
        sleep(0.2)

        return Path(path)

    async def download_search_result_async(
        self, yt: YouTube, result_number: int = 0
    ) -> Path:
        path = await asyncio.get_event_loop().run_in_executor(
            self.executor, self.download_search_result, result_number, yt
        )
        self.paths.append(path)

        return path

    async def download_async(self, yts: List[YouTube]) -> List[Path]:
        tasks = []
        for i, yt in enumerate(yts):
            tasks.append(self.download_search_result_async(yt, i))

        res: List[Path] = list(await asyncio.gather(*tasks))
        return [x for x in res if x is not None]

    def cleanup(self):
        for path in self.paths:
            if path.exists():
                path.unlink()
