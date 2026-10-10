"""Smoke tests for the HTTP API. They never load an AI model or touch the network."""
import pytest
from sqlalchemy import inspect

VALID_ID = "v4t0E3S1N1k"
BAD_IDS = ["../../etc/passwd", "a;b|c&d$e", "tooshort", "waytoolongvideoid", "abc def ghi", "v4t0E3S1N1!"]


def test_root(client):
    assert client.get("/").status_code == 200


def test_tables_created_on_startup(client):
    from database import engine
    assert {"videos", "transcripts", "dub_status"} <= set(inspect(engine).get_table_names())


@pytest.mark.parametrize("bad_id", BAD_IDS)
def test_bad_video_ids_are_rejected_everywhere(client, bad_id):
    assert client.post("/synthesize/", json={"video_id": bad_id}).status_code == 422
    assert client.post("/translate/", json={"video_id": bad_id, "tgt_lang": "jpn_Jpan"}).status_code == 422
    assert client.post("/text_to_speech/dub", json={"video_id": bad_id, "lang_code": "jpn_Jpan"}).status_code == 422
    assert client.get("/text_to_speech/dub_status", params={"video_id": bad_id}).status_code == 422


def test_transcribing_an_unfetched_video_is_a_clean_error(client):
    response = client.post("/synthesize/", json={"video_id": VALID_ID})
    assert response.status_code == 200
    assert "error" in response.json()


def test_dubbing_a_missing_video_is_404(client):
    response = client.post("/text_to_speech/dub", json={"video_id": VALID_ID, "lang_code": "jpn_Jpan", "segments": []})
    assert response.status_code == 404


def test_polling_an_unknown_dub_does_not_crash(client):
    response = client.get("/text_to_speech/dub_status", params={"video_id": VALID_ID})
    assert response.status_code == 200
    assert response.json() == {"status": "not_found"}


def test_a_bad_youtube_url_is_reported_not_downloaded(client):
    response = client.post("/videos/yt_video", json={"url": "https://example.com/not-youtube"})
    assert response.status_code == 200
    assert "error" in response.json()


def test_settings_start_unloaded(client):
    data = client.get("/settings/device").json()
    assert data["is_ready"] is False
    assert data["whisper_model"] is None and data["nllb_model"] is None
    assert "default_whisper_model" in data and "default_nllb_model" in data


def test_setup_rejects_unknown_models(client):
    response = client.post("/settings/setup", json={"device": "cpu", "whisper_model": "nope", "nllb_model": "x/y"})
    assert "error" in response.json()
    assert client.get("/settings/status").json()["stage"] == "idle"


def test_changing_a_model_before_setup_is_refused(client):
    client.post("/settings/whisper_model", json={"model_size": "tiny"})
    status = client.get("/settings/status").json()
    assert status["stage"] == "error"
    assert "set up" in status["error"].lower()


def test_preflight_report_shape(client):
    data = client.get("/settings/preflight").json()
    assert isinstance(data["ok"], bool)
    assert {c["name"] for c in data["checks"]} >= {"ffmpeg", "ffprobe"}
    assert all({"name", "ok", "optional", "hint"} <= set(c) for c in data["checks"])
    # an optional check (e.g. Korean) must never make the overall report fail
    assert data["ok"] == all(c["ok"] for c in data["checks"] if not c["optional"])


def test_cors_allows_only_configured_origins(client):
    ok = client.options("/", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    other = client.options("/", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in other.headers
