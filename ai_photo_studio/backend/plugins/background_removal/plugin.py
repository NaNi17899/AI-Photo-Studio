"""
Background Removal Plugin.
Uses rembg (U2NET) as primary engine with edge refinement,
custom background replacement, and shadow preservation.
"""

import os
import logging
import numpy as np
from PIL import Image

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.image_utils import (
    load_image_pil,
    save_image_pil,
    composite_on_background,
    refine_mask_edges,
)

logger = logging.getLogger(__name__)


class BackgroundRemovalPlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="background_removal",
            display_name="Background Removal",
            description="Remove backgrounds from photos with edge refinement. Works for portraits, products, and complex objects.",
            icon="✂️",
            category="editing",
            required_models=["rembg"],
            estimated_vram_mb=300,
            supports_batch=True,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "output_mode": {
                    "type": "string",
                    "enum": ["transparent", "white", "custom_color", "custom_image"],
                    "default": "transparent",
                    "title": "Output Mode",
                    "description": "Background for the output image",
                },
                "bg_color": {
                    "type": "string",
                    "default": "#FFFFFF",
                    "title": "Background Color",
                    "description": "Hex color for custom_color mode",
                },
                "bg_image_path": {
                    "type": "string",
                    "default": "",
                    "title": "Background Image Path",
                    "description": "Path to background image for custom_image mode",
                },
                "edge_refinement": {
                    "type": "boolean",
                    "default": True,
                    "title": "Edge Refinement",
                    "description": "Apply edge smoothing to reduce halos",
                },
                "edge_blur": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 10,
                    "default": 1,
                    "title": "Edge Blur",
                    "description": "Blur radius for edge refinement",
                },
                "alpha_matting": {
                    "type": "boolean",
                    "default": True,
                    "title": "Alpha Matting",
                    "description": "Use alpha matting for hair-aware edges",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        # rembg manages its own model download, so we just register it
        def load_rembg():
            from rembg import new_session

            session = new_session("u2net")
            return session

        model_manager.register("rembg", load_rembg, vram_mb=300)

    def process(self, input_paths: list[str], params: dict, progress_cb) -> list[str]:
        from rembg import remove as rembg_remove

        output_mode = params.get("output_mode", "transparent")
        edge_refinement = params.get("edge_refinement", True)
        edge_blur = params.get("edge_blur", 1)
        alpha_matting = params.get("alpha_matting", True)
        bg_color_hex = params.get("bg_color", "#FFFFFF")
        bg_image_path = params.get("bg_image_path", "")

        outputs = []
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            try:
                progress_cb((i / total) * 100, f"Processing image {i + 1}/{total}...")

                img = load_image_pil(path).convert("RGBA")

                # Remove background with rembg
                removed = rembg_remove(
                    img,
                    alpha_matting=alpha_matting,
                    alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10,
                    alpha_matting_erode_size=10,
                )

                # Edge refinement
                if edge_refinement and edge_blur > 0:
                    alpha = removed.split()[3]
                    alpha_np = np.array(alpha)
                    alpha_np = refine_mask_edges(alpha_np, blur_radius=edge_blur)
                    removed.putalpha(Image.fromarray(alpha_np))

                # Apply background
                if output_mode == "transparent":
                    result = removed
                elif output_mode == "white":
                    result = composite_on_background(removed, background_color=(255, 255, 255))
                elif output_mode == "custom_color":
                    # Parse hex color
                    hex_color = bg_color_hex.lstrip("#")
                    r, g, b = (
                        int(hex_color[0:2], 16),
                        int(hex_color[2:4], 16),
                        int(hex_color[4:6], 16),
                    )
                    result = composite_on_background(removed, background_color=(r, g, b))
                elif (
                    output_mode == "custom_image"
                    and bg_image_path
                    and os.path.exists(bg_image_path)
                ):
                    bg_img = Image.open(bg_image_path)
                    result = composite_on_background(removed, background_image=bg_img)
                else:
                    result = removed

                # Save
                output_path = self.get_output_path(path, "_nobg")
                save_image_pil(result, output_path)
                outputs.append(output_path)

            except Exception as e:
                logger.error("Background removal failed for %s: %s", path, e)
                raise

        progress_cb(100, "Background removal complete")
        return outputs
