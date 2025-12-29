from diffusers.pipelines.pipeline_utils import DiffusionPipeline
from PIL import Image
import torch
import random
from typing import Optional, Tuple

# Lazy singletons to avoid reloading weights on every request
_base_pipe: Optional[DiffusionPipeline] = None
_refiner_pipe: Optional[DiffusionPipeline] = None


def _get_pipes() -> Tuple[DiffusionPipeline, DiffusionPipeline]:
    global _base_pipe, _refiner_pipe
    if _base_pipe is None:
        _base_pipe = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
        ).to("cuda")
    if _refiner_pipe is None:
        _refiner_pipe = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-refiner-1.0",
            text_encoder_2=_base_pipe.text_encoder_2,  # type: ignore
            vae=_base_pipe.vae,  # type: ignore
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16",
        ).to("cuda")
    return _base_pipe, _refiner_pipe


def generate_image(
    input_prompt="a futuristic city scape, intergalatic civilization floating through a colorful universe, stars and colorful nebula, award winning illustration, highly detailed, bold line work, bright saturated colors, beautiful composition, artstation, 8k",
) -> Image.Image:
    base, refiner = _get_pipes()

    # Define how many steps and what % of steps to be run on each experts (80/20) here
    n_steps = 35
    high_noise_frac = 0.8

    prompt = (
        input_prompt
        or "a futuristic city scape, intergalatic civilization floating through a colorful universe, stars and colorful nebula, award winning illustration, highly detailed, bold line work, bright saturated colors, beautiful composition, artstation, 8k"
    )
    negative_prompt = "ugly, grotesque, deformed, horrifying, blury, smeared, burnt, weird hands, bad hands, too many limbs, detached limbs"

    # run both experts
    base_image = base(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=n_steps,
        denoising_end=high_noise_frac,  # type: ignore
        output_type="latent",
    ).images  # type: ignore
    return refiner(
        prompt=prompt,
        num_inference_steps=n_steps,
        denoising_start=high_noise_frac,  # type: ignore
        image=base_image,
    ).images[0]  # type: ignore
