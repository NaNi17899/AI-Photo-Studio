"""
Cartoon & Anime Conversion Plugin.
Uses a lightweight cartoon style approach with edge detection + color quantization,
and optionally SD + anime LoRA for higher quality.
"""

import logging
import cv2
import numpy as np
from PIL import Image

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.model_manager import get_model_manager
from backend.core.image_utils import load_image_cv2, load_image_pil, save_image_pil, cv2_to_pil


logger = logging.getLogger(__name__)


def cartoonize_cv2(
    img_cv: np.ndarray, num_colors: int = 9, line_size: int = 7, blur_value: int = 7
) -> np.ndarray:
    """
    Cartoonize an image using edge detection + bilateral filter + color quantization.
    Lightweight, no GPU required.
    """
    # Edge detection
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, blur_value)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, line_size, blur_value
    )

    # Color quantization with k-means
    data = np.float32(img_cv).reshape((-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)
    _, label, center = cv2.kmeans(data, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    quantized = center[label.flatten()].reshape(img_cv.shape)

    # Bilateral filter for smooth look
    blurred = cv2.bilateralFilter(quantized, d=7, sigmaColor=200, sigmaSpace=200)

    # Combine edges with smoothed image
    cartoon = cv2.bitwise_and(blurred, blurred, mask=edges)

    return cartoon


class CartoonAnimePlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="cartoon_anime",
            display_name="Cartoon & Anime",
            description="Convert photos to cartoon or anime style. Fast mode uses edge detection, quality mode uses AI.",
            icon="🎌",
            category="creative",
            required_models=[],
            estimated_vram_mb=0,
            supports_batch=True,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["cartoon_fast", "anime_sd"],
                    "default": "cartoon_fast",
                    "title": "Mode",
                    "description": "Fast cartoon (no GPU) or AI anime (requires SD)",
                },
                "num_colors": {
                    "type": "integer",
                    "minimum": 4,
                    "maximum": 20,
                    "default": 9,
                    "title": "Color Palette Size",
                    "description": "Number of colors in cartoon (fewer = more stylized)",
                },
                "line_thickness": {
                    "type": "integer",
                    "enum": [3, 5, 7, 9, 11],
                    "default": 7,
                    "title": "Line Thickness",
                    "description": "Edge line thickness for cartoon mode",
                },
                "anime_prompt": {
                    "type": "string",
                    "default": "anime style, high quality anime art, detailed, vibrant colors",
                    "title": "Anime Prompt",
                    "description": "Style prompt for anime SD mode",
                },
                "strength": {
                    "type": "number",
                    "minimum": 0.3,
                    "maximum": 0.9,
                    "default": 0.65,
                    "title": "AI Strength",
                    "description": "Transformation strength for anime SD mode",
                },
                "face_preserve": {
                    "type": "boolean",
                    "default": True,
                    "title": "Preserve Faces",
                    "description": "Try to preserve face structure",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        # Cartoon fast mode doesn't need models
        # Anime SD mode reuses the stable_diffusion model from style_transfer
        pass

    def process(self, input_paths: list[str], params: dict, progress_cb) -> list[str]:

        mode = params.get("mode", "cartoon_fast")

        if mode == "cartoon_fast":
            return self._process_cartoon(input_paths, params, progress_cb)
        else:
            return self._process_anime_sd(input_paths, params, progress_cb)

    def _process_cartoon(self, input_paths, params, progress_cb):
        num_colors = params.get("num_colors", 9)
        line_size = params.get("line_thickness", 7)

        outputs = []
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            try:
                progress_cb((i / total) * 100, f"Cartoonizing {i + 1}/{total}...")

                img_cv = load_image_cv2(path)
                if img_cv.shape[2] == 4:
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGRA2BGR)

                cartoon = cartoonize_cv2(img_cv, num_colors=num_colors, line_size=line_size)

                result = cv2_to_pil(cartoon)
                output_path = self.get_output_path(path, "_cartoon")
                save_image_pil(result, output_path)
                outputs.append(output_path)

            except Exception as e:
                logger.error("Cartoon conversion failed for %s: %s", path, e)
                raise

        progress_cb(100, "Cartoon conversion complete")
        return outputs

    def _process_anime_sd(self, input_paths, params, progress_cb):
        """Use Stable Diffusion with anime-tuned settings."""
        from backend.core.image_utils import resize_to_max

        mm = get_model_manager()
        prompt = params.get("anime_prompt", "anime style, high quality anime art")
        strength = params.get("strength", 0.65)

        progress_cb(5, "Loading Stable Diffusion for anime mode...")
        pipe = mm.load_sync("stable_diffusion")

        outputs = []
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            try:
                progress_cb(10 + (i / total) * 80, f"Anime conversion {i + 1}/{total}...")

                img = load_image_pil(path).convert("RGB")
                img = resize_to_max(img, 512)
                w, h = img.size
                w = (w // 8) * 8
                h = (h // 8) * 8
                img = img.resize((w, h), Image.LANCZOS)

                result = pipe(
                    prompt=prompt,
                    negative_prompt="realistic, photo, low quality, blurry",
                    image=img,
                    strength=strength,
                    num_inference_steps=25,
                    guidance_scale=8.0,
                ).images[0]

                output_path = self.get_output_path(path, "_anime")
                save_image_pil(result, output_path)
                outputs.append(output_path)

            except Exception as e:
                logger.error("Anime conversion failed for %s: %s", path, e)
                raise

        progress_cb(100, "Anime conversion complete")
        return outputs
