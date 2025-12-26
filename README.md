# dev-text2video

Development workspace for the text-to-video proxy/backend.

## Requirements
- Docker + GPU recommended
- Built/tested on **aarch64**. For x86_64, choose the matching base image tag and rebuild locally.

## Build
```bash
docker build -t inference/text2video:local .
```

## Run (standalone)
```bash
docker run --gpus all -d -p 7102:7102 inference/text2video:local
```

## Run with docker-compose (root of repo)
```bash
docker compose up text2video
```

## Notes
- Exposes API_PORT default 7102 (see docker-compose)
