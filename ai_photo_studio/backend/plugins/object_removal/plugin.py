"""
Object Removal Plugin.
Uses LaMa for inpainting with user-drawn masks.
"""

import os
import logging
import numpy as np
from PIL import Image

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.model_manager import get_model_manager
from backend.core.image_utils import load_image_pil, save_image_pil

logger = logging.getLogger(__name__)


class ObjectRemovalPlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="object_removal",
            display_name="Object Removal",
            description="Remove unwanted objects from photos using AI inpainting. Draw a mask over the area to remove.",
            icon="🧹",
            category="editing",
            required_models=["lama"],
            estimated_vram_mb=300,
            supports_batch=False,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "mask_path": {
                    "type": "string",
                    "title": "Mask Image Path",
                    "description": "Path to mask image (white = remove, black = keep)",
                },
                "mask_data": {
                    "type": "string",
                    "title": "Mask Data",
                    "description": "Base64-encoded mask image from canvas drawing",
                },
                "dilate_mask": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 30,
                    "default": 5,
                    "title": "Mask Dilation",
                    "description": "Expand mask edges to ensure clean removal",
                },
                "passes": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 3,
                    "default": 1,
                    "title": "Inpainting Passes",
                    "description": "Multiple passes for better quality on large areas",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        def load_lama():
            from simple_lama_inpainting import SimpleLama

            return SimpleLama()

        model_manager.register("lama", load_lama, vram_mb=300)

    def process(self, input_paths: list[str], params: dict, progress_cb) -> list[str]:
        import base64
        from io import BytesIO

        mask_path = params.get("mask_path", "")
        mask_data_b64 = params.get("mask_data", "")
        dilate_mask = params.get("dilate_mask", 5)
        passes = params.get("passes", 1)

        mm = get_model_manager()
        lama = mm.load_sync("lama")

        outputs = []

        for i, path in enumerate(input_paths):
            try:
                progress_cb(10, "Loading image and mask...")

                img = load_image_pil(path).convert("RGB")

                # Load mask from path or base64 data
                if mask_data_b64:
                    mask_bytes = base64.b64decode(mask_data_b64)
                    mask = Image.open(BytesIO(mask_bytes)).convert("L")
                elif mask_path and os.path.exists(mask_path):
                    mask = Image.open(mask_path).convert("L")
                else:
                    raise ValueError("No mask provided. Draw a mask over the area to remove.")

                # Resize mask to match image
                if mask.size != img.size:
                    mask = mask.resize(img.size, Image.NEAREST)

                # Dilate mask to ensure clean edges
                if dilate_mask > 0:
                    import cv2

                    mask_np = np.array(mask)
                    kernel = np.ones((dilate_mask * 2, dilate_mask * 2), np.uint8)
                    mask_np = cv2.dilate(mask_np, kernel, iterations=1)
                    mask = Image.fromarray(mask_np)

                # Run LaMa inpainting
                result = img
                for p in range(passes):
                    progress_cb(20 + (p / passes) * 70, f"Inpainting pass {p + 1}/{passes}...")
                    result = lama(result, mask)

                output_path = self.get_output_path(path, "_removed")
                save_image_pil(result, output_path)
                outputs.append(output_path)

            except Exception as e:
                logger.error("Object removal failed for %s: %s", path, e)
                raise

        progress_cb(100, "Object removal complete")
        return outputs
