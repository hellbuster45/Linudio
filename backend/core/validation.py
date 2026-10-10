import re
from typing import Annotated
from pydantic import StringConstraints

# YouTube video ids are exactly 11 chars from this alphabet. The id ends up in
# file paths and subprocess arguments, so anything else must be rejected up front.
VIDEO_ID_PATTERN = r"^[A-Za-z0-9_-]{11}$"
_VIDEO_ID_RE = re.compile(VIDEO_ID_PATTERN)

VideoId = Annotated[str, StringConstraints(pattern=VIDEO_ID_PATTERN)]

def is_valid_video_id(value: str | None) -> bool:
    return bool(value) and _VIDEO_ID_RE.fullmatch(value) is not None
