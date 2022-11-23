import asyncio
import json
from asyncio import Semaphore
from concurrent.futures import _base
from pathlib import Path

import ffmpeg


class Converter:
    def __init__(self, executor: _base.Executor):
        self.executor = executor
        self.semaphore = Semaphore(5)
        self.normalize = False

    def first_pass(self, input_path: Path) -> dict:
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.filter(stream, "loudnorm", print_format="json")
        stream = stream.output("-", f="null")
        _, out = stream.run(capture_stderr=True)
        out = out.decode()
        jsn = "{" + out.split("{")[1].split("}")[0] + "}"

        return json.loads(jsn)

    def to_mp3(self, input_path: Path, output_path: Path):
        stream = ffmpeg.input(input_path)

        if self.normalize:
            first_pass = self.first_pass(input_path)
            stream = stream.filter(
                "loudnorm",
                I=-11.0,
                LRA=7.0,
                TP=-1.0,
                measured_I=first_pass["input_i"],
                measured_LRA=first_pass["input_lra"],
                measured_TP=first_pass["input_tp"],
                measured_thresh=first_pass["input_thresh"],
                print_format="json",
            )

        stream = stream.output(str(output_path))
        stream.run(quiet=True, overwrite_output=True)

    async def to_mp3_async(self, input_path: Path, output_path: Path):
        async with self.semaphore:
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.to_mp3, input_path, output_path
            )
