"""First-time setup planning and the worker protocol, without loading any model."""
import asyncio
import json

import pytest

from api.v1.settings import services as setup_services
from api.v1.tts.services import _read_result


def test_all_voices_by_default():
    assert setup_services.resolve_voices(None, korean_available=True) == ["EN", "ES", "FR", "ZH", "JP", "KR"]


def test_korean_is_dropped_when_its_tokenizer_is_missing():
    assert "KR" not in setup_services.resolve_voices(None, korean_available=False)
    assert "KR" not in setup_services.resolve_voices(["EN", "KR"], korean_available=False)


def test_requested_voices_keep_the_standard_order():
    assert setup_services.resolve_voices(["JP", "EN"], korean_available=True) == ["EN", "JP"]
    assert setup_services.resolve_voices([], korean_available=True) == []


def test_steps_cover_everything_in_a_sensible_order():
    steps = setup_services.plan_setup_steps(
        "tiny", "facebook/nllb-200-distilled-600M", ["EN", "JP"],
        dictionary_missing=True, english_data_missing=True,
    )
    keys = [k for k, _ in steps]
    assert keys == ["dictionary", "english_data", "whisper", "nllb", "separator", "voice:EN", "voice:JP"]
    assert dict(steps)["whisper"] == "Transcription model: tiny"
    assert dict(steps)["voice:JP"] == "Voice: Japanese"


def test_steps_skip_what_is_already_in_place():
    steps = setup_services.plan_setup_steps("tiny", "m", ["ES"], dictionary_missing=False, english_data_missing=True)
    assert [k for k, _ in steps] == ["whisper", "nllb", "separator", "voice:ES"]  # no English voice, so no English data


def test_english_data_step_only_when_english_is_requested():
    steps = setup_services.plan_setup_steps("tiny", "m", ["EN"], dictionary_missing=False, english_data_missing=True)
    assert "english_data" in [k for k, _ in steps]


def test_setup_rejects_unknown_voices(client):
    response = client.post("/settings/setup", json={
        "device": "cpu", "whisper_model": "tiny",
        "nllb_model": "facebook/nllb-200-distilled-600M", "voices": ["EN", "XX"],
    })
    assert "error" in response.json() and "XX" in response.json()["error"]


def _stream(*lines: str) -> asyncio.StreamReader:
    reader = asyncio.StreamReader()
    for line in lines:
        reader.feed_data((line + "\n").encode("utf-8"))
    reader.feed_eof()
    return reader


async def test_events_are_forwarded_and_the_result_returned():
    events = []
    reader = _stream(
        json.dumps({"event": "voice", "lang": "EN"}),
        json.dumps({"event": "progress", "downloaded": 5, "total": 10}),
        json.dumps({"status": "ok"}),
    )
    result = await _read_result(reader, events.append)
    assert result == {"status": "ok"}
    assert events == [{"event": "voice", "lang": "EN"}, {"event": "progress", "downloaded": 5, "total": 10}]


async def test_stray_output_does_not_break_the_protocol():
    reader = _stream("loading weights...", "[1, 2, 3]", json.dumps({"status": "ok"}))
    assert await _read_result(reader) == {"status": "ok"}


async def test_a_dead_worker_returns_none():
    assert await _read_result(_stream()) is None


def test_only_one_load_at_a_time(client):
    from core.progress import set_status
    set_status("loading", target="Something")
    try:
        for path, body in [
            ("/settings/setup", {"device": "cpu", "whisper_model": "tiny", "nllb_model": "facebook/nllb-200-distilled-600M"}),
            ("/settings/device", {"device": "cpu"}),
            ("/settings/whisper_model", {"model_size": "tiny"}),
            ("/settings/nllb_model", {"model_name": "facebook/nllb-200-distilled-600M"}),
        ]:
            response = client.post(path, json=body).json()
            assert "still being set up" in response["error"], path
        assert client.get("/settings/status").json()["target"] == "Something"  # untouched by the refused requests
    finally:
        set_status("idle")
