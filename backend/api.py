"""Bounded asynchronous API for the text-to-video inference pipeline."""
from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

DATA_DIR = Path(os.getenv("DATA_DIR", "/data")).resolve()
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "2000"))
MAX_JOBS = int(os.getenv("MAX_JOBS", "64"))
WORKERS = int(os.getenv("WORKERS", "1"))
API_KEY = os.getenv("API_KEY")
MODEL_ID = os.getenv("VIDEO_MODEL_ID", "stabilityai/stable-video-diffusion-img2vid-xt")
IMAGE_MODEL_ID = os.getenv("IMAGE_MODEL_ID", "stabilityai/stable-diffusion-xl-base-1.0")
MOCK_INFERENCE = os.getenv("MOCK_INFERENCE", "false").lower() in {"1", "true", "yes"}

DATA_DIR.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="dev-text2video backend", version="1.0.0")
executor = ThreadPoolExecutor(max_workers=max(1, WORKERS), thread_name_prefix="inference")
jobs: dict[str, dict] = {}
lock = threading.Lock()


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_CHARS)


class Job(BaseModel):
    id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    created_at: float
    error: str | None = None
    media_url: str | None = None


def authorize(authorization: str | None) -> None:
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="invalid bearer token")


def public_job(record: dict) -> Job:
    return Job(**{key: record.get(key) for key in Job.model_fields})


def run_job(job_id: str, prompt: str) -> None:
    with lock:
        jobs[job_id]["status"] = "running"
    try:
        output = DATA_DIR / f"{job_id}.mp4"
        if MOCK_INFERENCE:
            output.write_bytes(b"mock-mp4")
        else:
            # Heavy ML modules are imported only inside the worker. Importing the API,
            # health checks, and CI never downloads or allocates a model.
            from main import generate_to_path
            generate_to_path(prompt, output, IMAGE_MODEL_ID, MODEL_ID)
        with lock:
            jobs[job_id].update(status="succeeded", media_url=f"/v1/jobs/{job_id}/media")
    except Exception as exc:  # worker failures are represented by the job contract
        with lock:
            jobs[job_id].update(status="failed", error=str(exc)[:1000])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    # Writable storage is required; actual model loading remains explicit and costly.
    probe = DATA_DIR / ".ready"
    try:
        probe.touch(exist_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"data directory unavailable: {exc}")
    return {"ready": True, "mock": MOCK_INFERENCE, "model": MODEL_ID}


@app.post("/v1/jobs", status_code=202, response_model=Job)
def generate(request: GenerateRequest, authorization: str | None = Header(default=None)) -> Job:
    authorize(authorization)
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="prompt cannot be blank")
    with lock:
        if sum(j["status"] in {"queued", "running"} for j in jobs.values()) >= MAX_JOBS:
            raise HTTPException(status_code=429, detail="job queue is full")
        job_id = str(uuid4())
        jobs[job_id] = {"id": job_id, "status": "queued", "created_at": time.time()}
        record = public_job(jobs[job_id])
    executor.submit(run_job, job_id, prompt)
    return record


def get_record(job_id: str) -> dict:
    try:
        UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="job not found")
    with lock:
        record = jobs.get(job_id)
        if not record:
            raise HTTPException(status_code=404, detail="job not found")
        return dict(record)


@app.get("/v1/jobs/{job_id}", response_model=Job)
def get_job(job_id: str, authorization: str | None = Header(default=None)) -> Job:
    authorize(authorization)
    return public_job(get_record(job_id))


@app.get("/v1/jobs/{job_id}/media")
def get_media(job_id: str, authorization: str | None = Header(default=None)) -> FileResponse:
    authorize(authorization)
    record = get_record(job_id)
    if record["status"] != "succeeded":
        raise HTTPException(status_code=409, detail="media is not ready")
    path = DATA_DIR / f"{job_id}.mp4"
    if not path.is_file():
        raise HTTPException(status_code=410, detail="media expired")
    return FileResponse(path, media_type="video/mp4", filename=f"{job_id}.mp4")
