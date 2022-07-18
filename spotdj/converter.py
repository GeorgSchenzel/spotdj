import asyncio
from asyncio import Semaphore
from concurrent.futures import _base
from pathlib import Path

import ffmpeg


class Converter:
    def __init__(self, executor: _base.Executor):
        self.executor = executor
        self.semaphore = Semaphore(5)

    def to_mp3(self, input_path: Path, output_path: Path):
        (
            ffmpeg
            .input(input_path)
            .output(str(output_path))
            .run(quiet=True, overwrite_output=True)
        )

    async def to_mp3_async(self, input_path: Path, output_path: Path):
        async with self.semaphore:
            await asyncio.get_event_loop().run_in_executor(self.executor, self.to_mp3, input_path, output_path)
