# dev-text2video

A bounded, asynchronous text-to-video service built around Stable Diffusion XL and Stable Video Diffusion. It preserves the original ARM64 work while providing the same container/API contract on ARM64 and x86-64, CPU or NVIDIA GPU.

> Video diffusion is extremely expensive on CPU. CPU mode is supported for portability and contract testing; NVIDIA is the practical production target.

## API

- `GET /health`: process liveness
- `GET /ready`: storage/config readiness (does not download weights)
- `POST /v1/jobs`: submit `{ "prompt": "..." }`, returns `202`
- `GET /v1/jobs/{id}`: poll `queued`, `running`, `succeeded`, or `failed`
- `GET /v1/jobs/{id}/media`: stream the completed MP4

Set `API_KEY` to require `Authorization: Bearer <key>` on all job and media routes. Prompts are limited to 2,000 characters by default, the queue is bounded by `MAX_JOBS`, and inference is single-worker by default to avoid GPU oversubscription. Generated files use server-selected UUID names; clients cannot choose filesystem paths.

```bash
docker compose up --build text2video                 # portable CPU
docker compose --profile nvidia up --build text2video-nvidia
```

Use an existing Hugging Face cache without copying it:

```bash
MODEL_CACHE="$HOME/.cache/huggingface" docker compose up text2video
```

`MODEL_CACHE` may be a host path or a Docker volume. `OUTPUT_DIR` defaults to `./outputs`. Pin reproducible model revisions in a pre-populated cache or replace `VIDEO_MODEL_ID` and `IMAGE_MODEL_ID` with an internal immutable model path. The default upstream IDs are intentionally configurable because model artifacts are not committed here.

Example:

```bash
job=$(curl -fsS -X POST http://localhost:7102/v1/jobs \
  -H 'content-type: application/json' \
  -d '{"prompt":"a paper spaceship drifting through clouds"}')
echo "$job"
curl -fsS http://localhost:7102/v1/jobs/JOB_ID
curl -fLo result.mp4 http://localhost:7102/v1/jobs/JOB_ID/media
```

## Development

The smoke tests use `MOCK_INFERENCE=true`; they validate the full job/media contract without downloading multi-gigabyte weights.

```bash
python -m venv backend/.venv
backend/.venv/bin/pip install './backend[test]'
(cd backend && .venv/bin/pytest -q)
cargo test --locked
docker compose config --quiet
```

The legacy Rust proxy remains build-tested for compatibility, but the production container exposes FastAPI directly, avoiding two competing supervisors and response buffering. Model loading is lazy: health/readiness and CI never allocate a GPU or trigger downloads.
