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

    async def select(self, default: Path) -> Path:
        self.cancel()

        async with self.lock:
            with patch_stdout():
                self.task = asyncio.create_task(self.session.prompt_async('Filename: ', default=str(default)))

                try:
                    return Path(await self.task)
                except CancelledError:
                    return default
