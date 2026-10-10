import sys

import pytest

from api.v1.helpers import extract_youtube_id, is_youtube_url, get_metadata
from core.proc import run_command
from core.validation import is_valid_video_id


@pytest.mark.parametrize("value,expected", [
    ("v4t0E3S1N1k", True), ("-_AZaz09-_x", True),
    ("", False), (None, False), ("short", False), ("has space!!", False), ("a;b|c&d$e1", False),
])
def test_is_valid_video_id(value, expected):
    assert is_valid_video_id(value) is expected


@pytest.mark.parametrize("url,expected", [
    ("https://www.youtube.com/watch?v=v4t0E3S1N1k", "v4t0E3S1N1k"),
    ("https://youtu.be/v4t0E3S1N1k", "v4t0E3S1N1k"),
    ("https://www.youtube.com/watch?v=v4t0E3S1N1k&t=10", "v4t0E3S1N1k"),
    ("https://www.youtube.com/watch?v=bad;id|x&y", None),
    ("https://youtu.be/v4t0E3S1N1k?si=abc", "v4t0E3S1N1k"),
    ("https://www.youtube.com/embed/v4t0E3S1N1k", "v4t0E3S1N1k"),
    ("https://www.youtube.com/shorts/v4t0E3S1N1k", "v4t0E3S1N1k"),
    ("https://youtu.be/abcdefghijk", "abcdefghijk"),
    ("https://www.youtube.com/playlist?list=PL123", None),
    ("https://example.com/", None),
])
def test_extract_youtube_id(url, expected):
    assert extract_youtube_id(url) == expected


async def test_run_command_never_interprets_shell_syntax():
    nasty = "a;b|c&d $HOME `x` $(y) \"q\" 'r'"
    code, out = await run_command([sys.executable, "-c", "import sys; print(sys.argv[1])", nasty], "test")
    assert code == 0
    assert out.strip() == nasty


async def test_run_command_reports_missing_executable():
    code, out = await run_command(["definitely-not-a-real-program-xyz"], "test")
    assert code == -1 and out == ""


async def test_run_command_returns_failure_code():
    code, _ = await run_command([sys.executable, "-c", "import sys; sys.exit(3)"], "test")
    assert code == 3


@pytest.mark.parametrize("url,expected", [
    ("https://www.youtube.com/watch?v=v4t0E3S1N1k", True),
    ("youtube.com/watch?v=v4t0E3S1N1k", True),
    ("https://youtu.be/v4t0E3S1N1k", True),
    ("https://evil.example/watch?v=v4t0E3S1N1k", False),
    ("http://localhost:8000/watch?v=v4t0E3S1N1k", False),
    ("https://www.youtube.com.evil.example/watch?v=v4t0E3S1N1k", False),
    ("file:///etc/passwd", False),
])
def test_only_youtube_hosts_are_accepted(url, expected):
    assert is_youtube_url(url) is expected


def test_metadata_rejects_non_youtube_urls_without_touching_the_network():
    result = get_metadata("https://evil.example/watch?v=v4t0E3S1N1k")
    assert "error" in result and "video_id" not in result
