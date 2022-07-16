import asyncio
import concurrent.futures
import subprocess
import time
from pathlib import Path

import ffmpeg
import mutagen
from python_telnet_vlc import VLCTelnet
from pytube import Search, YouTube
from pytube.query import StreamQuery


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


def download(nr: int, yt: YouTube):
    streams = StreamQuery(yt.fmt_streams)
    audio_stream = streams.get_audio_only()
    path = audio_stream.download()

    mutagen_file = mutagen.File(path, easy=True)
    mutagen_file["artist"] = yt.author
    mutagen_file["tracknumber"] = str(nr)
    mutagen_file["description"] = "Bitrate: {}, Views: {}".format(audio_stream.abr, human_format(yt.views))
    mutagen_file.save()

    return path


async def download_pooled(nr: int, yt: YouTube):
    return await loop.run_in_executor(thread_executor, download, nr, yt)


async def _aggregate_tasks(tasks):
    """
    Aggregate the futures and return the results
    """

    return await asyncio.gather(*(task for task in tasks))


def create_file_name():
    return "{artist} - {title}.{ext}".format(artist="Robbie Doherty & Keees.", title="Pour The Milk", ext="mp3")

options_to_show = 5

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

semaphore = asyncio.Semaphore(10)

server = subprocess.Popen(["vlc", "--extraintf", "telnet", "--telnet-host", "127.0.0.1", "--telnet-port", "4212", "--telnet-password", "password"], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
v = VLCTelnet("127.0.0.1", "password", 4212)

results = Search("Robbie Doherty & Keees. - Pour The Milk").results

tasks = []
for i in range(options_to_show):
    yt = results[i]
    tasks.append(download_pooled(i, yt))

paths = list(loop.run_until_complete(_aggregate_tasks(tasks)))

for path in paths:
    v.enqueue(path)

# keep alive
playing = {"playing", "stopped"}
while v.status()["state"] in playing:
    time.sleep(0.5)

nr = v.info()["data"]["track_number"]

v.clear()

chosen_path = paths[int(nr)]
(
    ffmpeg
    .input(chosen_path)
    .output(create_file_name())
    .run(quiet=True, overwrite_output=True)
)

for path in paths:
    Path(path).unlink()

v.shutdown()


