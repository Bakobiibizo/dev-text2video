"""Inference adapter. Model implementations remain replaceable behind one contract."""
from pathlib import Path


def generate_to_path(prompt: str, output: Path, image_model_id: str, video_model_id: str) -> None:
    from src.stable_diffusion_xl import generate_image
    from src.stable_video_xt import generate_video

    image_path = output.with_suffix(".png")
    image = generate_image(prompt, model_id=image_model_id)
    image.save(image_path)
    generate_video(image_path=str(image_path), video_path=str(output), fps=8, model_id=video_model_id)
