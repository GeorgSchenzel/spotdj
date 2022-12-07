import subprocess

from python_telnet_vlc import VLCTelnet


class VlcPlayer:
    def __init__(self):
        self.server = subprocess.Popen(
            [
                "vlc",
                "--extraintf",
                "telnet",
                "--telnet-host",
                "127.0.0.1",
                "--telnet-port",
                "4212",
                "--telnet-password",
                "password",
            ],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.client = VLCTelnet("127.0.0.1", "password", 4212)

    def stop(self):
        self.client.shutdown()

    def is_paused(self) -> bool:
        return self.client.status()["state"] == "paused"
