from pathlib import Path

import ffmpeg


class Converter:
    def __init__(self):
        pass

    def to_mp3(self, input_path: Path, output_path: Path):
        (
            ffmpeg
            .input(input_path)
            .output(str(output_path))
            .run(quiet=True, overwrite_output=True)
        )
