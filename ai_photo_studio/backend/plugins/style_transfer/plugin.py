"""
Style Transfer Plugin.
Uses Stable Diffusion 1.5 img2img with LoRA support.
Optimized for GTX 1650 (4GB VRAM) with CPU offloading.
"""

import os
import logging
from PIL import Image

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.model_manager import get_model_manager
from backend.core.image_utils import load_image_pil, save_image_pil, resize_to_max
from backend.core.gpu_utils import get_device


logger = logging.getLogger(__name__)


class StyleTransferPlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="style_transfer",
            display_name="Style Transfer",
            description="Transform photo styles using Stable Diffusion img2img with LoRA support. Requires ~3.5GB VRAM.",
            icon="🎭",
            category="creative",
            required_models=["stable_diffusion"],
            estimated_vram_mb=3500,
            supports_batch=True,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "default": "professional photo, high quality, detailed",
                    "title": "Style Prompt",
                    "description": "Describe the desired style",
                },
                "negative_prompt": {
                    "type": "string",
                    "default": "low quality, blurry, distorted, deformed",
                    "title": "Negative Prompt",
                    "description": "What to avoid",
                },
                "strength": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 0.9,
                    "default": 0.5,
                    "title": "Style Strength",
                    "description": "How much to transform (0.1 = subtle, 0.9 = dramatic)",
                },
                "steps": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 50,
                    "default": 25,
                    "title": "Inference Steps",
                    "description": "More steps = better quality, slower",
                },
                "guidance_scale": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 15.0,
                    "default": 7.5,
                    "title": "Guidance Scale",
                    "description": "How closely to follow the prompt",
                },
                "lora_path": {
                    "type": "string",
                    "default": "",
                    "title": "LoRA Model Path",
                    "description": "Path to .safetensors LoRA file",
                },
                "lora_scale": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 1.5,
                    "default": 0.8,
                    "title": "LoRA Scale",
                    "description": "LoRA influence strength",
                },
                "max_size": {
                    "type": "integer",
                    "minimum": 256,
                    "maximum": 768,
                    "default": 512,
                    "title": "Max Image Size",
                    "description": "Max dimension for processing (lower = faster, less VRAM)",
                },
                "seed": {
                    "type": "integer",
                    "default": -1,
                    "title": "Seed",
                    "description": "Random seed (-1 for random)",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        def load_sd():
            """Load Stable Diffusion 1.5 with aggressive memory optimization."""
            import torch
            from diffusers import StableDiffusionImg2ImgPipeline

            logger.info("Loading Stable Diffusion 1.5 (this may take a minute)...")

            pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16,
                safety_checker=None,
                requires_safety_checker=False,
            )

            # Aggressive memory optimization for GTX 1650
            device = get_device()
            if device == "cuda":
                pipe.enable_sequential_cpu_offload()
                pipe.enable_attention_slicing(1)
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    logger.info("xformers not available, using default attention")
            else:
                pipe = pipe.to("cpu")

            logger.info("Stable Diffusion loaded")
            return pipe

        model_manager.register("stable_diffusion", load_sd, vram_mb=3500)

    def process(self, input_paths: list[str], params: dict, progress_cb) -> list[str]:
        import torch

        prompt = params.get("prompt", "professional photo")
        negative_prompt = params.get("negative_prompt", "low quality, blurry")
        strength = params.get("strength", 0.5)
        steps = params.get("steps", 25)
        guidance = params.get("guidance_scale", 7.5)
        lora_path = params.get("lora_path", "")
        lora_scale = params.get("lora_scale", 0.8)
        max_size = params.get("max_size", 512)
        seed = params.get("seed", -1)

        mm = get_model_manager()

        # SD needs exclusive VRAM — unload other models
        progress_cb(5, "Loading Stable Diffusion (unloading other models)...")
        pipe = mm.load_sync("stable_diffusion")

        # Load LoRA if specified
        if lora_path and os.path.exists(lora_path):
            try:
                pipe.load_lora_weights(lora_path)
                pipe.fuse_lora(lora_scale=lora_scale)
                logger.info("Loaded LoRA: %s (scale=%.1f)", lora_path, lora_scale)
            except Exception as e:
                logger.warning("Failed to load LoRA: %s", e)

        outputs = []
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            try:
                progress_cb(10 + (i / total) * 80, f"Generating style {i + 1}/{total}...")

                img = load_image_pil(path).convert("RGB")
                img = resize_to_max(img, max_size)

                # Ensure dimensions are multiples of 8
                w, h = img.size
                w = (w // 8) * 8
                h = (h // 8) * 8
                img = img.resize((w, h), Image.LANCZOS)

                generator = None
                if seed >= 0:
                    generator = torch.Generator().manual_seed(seed)

                result = pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=img,
                    strength=strength,
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    generator=generator,
                ).images[0]

                output_path = self.get_output_path(path, "_styled")
                save_image_pil(result, output_path)
                outputs.append(output_path)

            except Exception as e:
                logger.error("Style transfer failed for %s: %s", path, e)
                raise

        # Unload LoRA if loaded
        if lora_path and os.path.exists(lora_path):
            try:
                pipe.unfuse_lora()
                pipe.unload_lora_weights()
            except Exception:
                pass

        progress_cb(100, "Style transfer complete")
        return outputs
