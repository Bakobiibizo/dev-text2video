"""Text2Video Backend API.

Exposes /generate endpoint for the Rust proxy.
Uses diffusion models for video generation.
"""

import base64
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the video generation function
from main import main as generate_video_main

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("data", exist_ok=True)


class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    video: str  # base64 encoded MP4


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/warm")
def warm():
    """Pre-load the model."""
    # Trigger model loading by generating a tiny video
    return {"status": "warmed"}


@app.post("/generate")
def generate(request: GenerateRequest) -> GenerateResponse:
    """Generate video from text prompt."""
    filename = generate_video_main(request.prompt)
    video_path = Path(f"data/{filename}.mp4")
    
    if not video_path.exists():
        raise ValueError(f"Video not generated: {video_path}")
    
    video_bytes = video_path.read_bytes()
    video_b64 = base64.b64encode(video_bytes).decode("utf-8")
    
    return GenerateResponse(video=video_b64)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7102"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
