import importlib
import time


def test_job_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MOCK_INFERENCE", "true")
    import api
    api = importlib.reload(api)
    from fastapi.testclient import TestClient
    with TestClient(api.app) as client:
        assert client.get("/health").status_code == 200
        response = client.post("/v1/jobs", json={"prompt": "a small robot waves"})
        assert response.status_code == 202
        job_id = response.json()["id"]
        for _ in range(50):
            job = client.get(f"/v1/jobs/{job_id}").json()
            if job["status"] == "succeeded":
                break
            time.sleep(.01)
        assert job["status"] == "succeeded"
        media = client.get(job["media_url"])
        assert media.status_code == 200
        assert media.content == b"mock-mp4"


def test_validation_and_auth(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MOCK_INFERENCE", "true")
    monkeypatch.setenv("API_KEY", "secret")
    import api
    api = importlib.reload(api)
    from fastapi.testclient import TestClient
    with TestClient(api.app) as client:
        assert client.post("/v1/jobs", json={"prompt": "x"}).status_code == 401
        assert client.post("/v1/jobs", headers={"Authorization": "Bearer secret"}, json={"prompt": " "}).status_code == 422
