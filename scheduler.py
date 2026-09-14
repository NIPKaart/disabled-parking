"""Run a finite collector command serially, with interruptible waits and a deadline."""

from __future__ import annotations

import argparse
import fcntl
import logging
import signal
import subprocess
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import FrameType

LOGGER = logging.getLogger(__name__)


def run_command(command: list[str], timeout: int, stopped: Event) -> bool:
    """Bound a child process and stop it before exiting the container."""
    with subprocess.Popen(command) as process:  # noqa: S603
        try:
            remaining = timeout
            while remaining > 0 and not stopped.is_set():
                try:
                    return process.wait(timeout=1) == 0
                except subprocess.TimeoutExpired:
                    remaining -= 1
            if not stopped.is_set():
                LOGGER.warning("Collector exceeded its deadline")
            return False
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def schedule(command: list[str], interval: int, timeout: int, stopped: Event) -> None:
    """Start immediately, then wait after each attempt; never overlap runs."""
    while not stopped.is_set():
        successful = run_command(command, timeout, stopped)
        if stopped.is_set():
            break
        if not successful:
            LOGGER.error(
                "Collector run failed; next attempt follows the configured wait"
            )
        stopped.wait(interval if successful else min(interval, 300))


def positive_seconds(value: str) -> int:
    """Reject zero or negative waits and deadlines."""
    seconds = int(value)
    if seconds <= 0:
        message = "Must be a positive number of seconds"
        raise argparse.ArgumentTypeError(message)
    return seconds


def main() -> None:
    """Hold a shared-volume lock while scheduling a trusted collector command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=positive_seconds, default=86400)
    parser.add_argument("--timeout", type=positive_seconds, default=300)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("A collector command is required after --")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    stopped = Event()

    def stop(_signum: int, _frame: FrameType | None) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        with args.lock.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            schedule(command, args.interval, args.timeout, stopped)
    except OSError as error:
        parser.exit(1, f"Scheduler unavailable: {error}\n")


if __name__ == "__main__":
    main()
