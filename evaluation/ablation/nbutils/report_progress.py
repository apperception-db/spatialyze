import socket
import subprocess
import os


def report_progress(progress: int, total: int, tag: str, message: str = ""):
    try:
        host = socket.gethostname()

        subprocess.run(
            [
                "ssh",
                "-o StrictHostKeyChecking=no",
                "-o UserKnownHostsFile=/dev/null",
                "chanwutk@" + os.environ["REPORT_IP"],
                "-t",
                f"touch ~/dashboard/progress__{host}.{tag} && echo {progress} {total} {message} > ~/dashboard/progress__{host}.{tag} && cd ~/dashboard && python3 update.py",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except:
        pass
