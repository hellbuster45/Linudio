"""Job-state handling around dubbing. The actual pipeline is stubbed out."""
import pytest

VIDEO_ID = "abcdefghijk"
PAYLOAD = {"video_id": VIDEO_ID, "lang_code": "jpn_Jpan", "segments": []}


@pytest.fixture
def dub_env(client, monkeypatch):
    import api.v1.tts.routes as routes
    from core.config import settings
    from database import SessionLocal
    from api.v1.tts.models import DubStatus

    async def no_pipeline(*args, **kwargs):
        return None

    monkeypatch.setattr(routes, "process_dubbing", no_pipeline)

    video_dir = settings.videos_dir / VIDEO_ID
    video_dir.mkdir(parents=True, exist_ok=True)
    (video_dir / f"{VIDEO_ID}_video.mp4").write_bytes(b"not a real video")

    db = SessionLocal()

    def set_status(status):
        row = db.query(DubStatus).filter_by(video_id=VIDEO_ID).first()
        if row is None:
            db.add(DubStatus(video_id=VIDEO_ID, status=status))
        else:
            row.status = status
        db.commit()

    yield set_status

    db.query(DubStatus).filter_by(video_id=VIDEO_ID).delete()
    db.commit()
    db.close()


def test_a_second_dub_while_one_is_running_is_refused(client, dub_env):
    dub_env("tts_generation")
    response = client.post("/text_to_speech/dub", json=PAYLOAD)
    assert response.status_code == 409


@pytest.mark.parametrize("old_status", ["failed", "complete"])
def test_a_finished_job_is_replaced_by_a_new_one(client, dub_env, old_status):
    dub_env(old_status)
    response = client.post("/text_to_speech/dub", json=PAYLOAD)
    assert response.status_code == 200 and response.json()["status"] == "started"
    assert client.get("/text_to_speech/dub_status", params={"video_id": VIDEO_ID}).json() == {"status": "pending"}


def test_failed_is_reported_once_then_cleared(client, dub_env):
    dub_env("failed")
    params = {"video_id": VIDEO_ID}
    assert client.get("/text_to_speech/dub_status", params=params).json() == {"status": "failed"}
    assert client.get("/text_to_speech/dub_status", params=params).json() == {"status": "not_found"}


def test_success_returns_a_relative_path_and_clears_the_job(client, dub_env):
    from core.config import settings
    (settings.videos_dir / VIDEO_ID / f"{VIDEO_ID}_dubbed.mp4").write_bytes(b"x")
    dub_env("complete")
    params = {"video_id": VIDEO_ID}
    body = client.get("/text_to_speech/dub_status", params=params).json()
    assert body == {"status": "success", "video_path": f"/storage/{VIDEO_ID}/{VIDEO_ID}_dubbed.mp4"}
    assert client.get("/text_to_speech/dub_status", params=params).json() == {"status": "not_found"}
