import asyncio
import os
import sys
from collections import deque

def _printable(text: str) -> str:
    # Child output can contain characters (e.g. progress-bar glyphs) that a Windows console
    # encoding can't display; round-trip through it with replacement so one unprintable
    # character can never crash the draining loop.
    enc = sys.stdout.encoding or "utf-8"
    return text.encode(enc, errors="replace").decode(enc, errors="replace")

async def run_command(args, task_name: str, *, stream_prefix: str | None = None, tail_lines: int = 20) -> tuple[int, str]:
    """Runs a command given as an argument list. Never goes through a shell, so file names
    and other arguments can't be interpreted as shell syntax.

    Returns (exit_code, stdout_text). If the executable can't be started the exit code is -1.
    Output is only printed live when `stream_prefix` is given; otherwise the last
    `tail_lines` lines are printed only if the command fails.
    """
    args = [str(a) for a in args]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            limit=1024 * 1024,  # progress bars can emit very long "lines"
        )
    except FileNotFoundError:
        print(f"[{task_name}] ERROR: '{args[0]}' was not found. Is it installed and on your PATH?")
        return -1, ""

    stdout_lines: list[str] = []
    tail: deque[str] = deque(maxlen=tail_lines)

    async def drain(stream, label, keep_stdout):
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode(errors="replace").rstrip()
            if keep_stdout:
                stdout_lines.append(text)
            tail.append(f"[{label}] {_printable(text)}")
            if stream_prefix:
                print(f"      [{stream_prefix}] {_printable(text)}")

    await asyncio.gather(drain(process.stdout, "OUT", True), drain(process.stderr, "ERR", False))
    returncode = await process.wait()

    if returncode != 0 and not stream_prefix:
        print(f"[{task_name}] failed (exit code {returncode}). Last output:")
        for line in tail:
            print(f"    {line}")

    return returncode, "\n".join(stdout_lines)
