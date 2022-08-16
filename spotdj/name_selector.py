import asyncio
from asyncio import Task, Lock, CancelledError
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


class NameSelector:
    def __init__(self):
        self.task: Task = None
        self.session = PromptSession()
        self.lock = Lock()

    def cancel(self):
        if self.task is not None:
            self.task.cancel()

    @staticmethod
    def smart_naming(file_name: str, download_name: str) -> str:
        if file_name.lower().endswith("mix") and file_name.count(" - ") > 1:
            file_name = " (".join(file_name.rsplit(" - ", 1)) + ")"

        if "extended" not in file_name.lower() and "extended" in download_name.lower():
            file_name += " (Extended Mix)"

        return file_name

    async def select(self, default: Path, downloaded: Path) -> Path:
        self.cancel()

        default = default.with_stem(NameSelector.smart_naming(default.stem, downloaded.stem))

        async with self.lock:
            with patch_stdout():
                self.task = asyncio.create_task(self.session.prompt_async('Filename: ', default=default.stem))

                try:
                    return default.with_stem(await self.task)
                except CancelledError:
                    return default
