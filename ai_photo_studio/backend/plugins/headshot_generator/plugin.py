"""
AI Headshot Generator Plugin.
Uses face enhancement + background removal + color grading
to generate professional headshots from casual photos.
"""

import os
import logging
import numpy as np
from PIL import Image

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.model_manager import get_model_manager
from backend.core.image_utils import (
    load_image_cv2,
    save_image_pil,
    cv2_to_pil,
    composite_on_background,
)


logger = logging.getLogger(__name__)


# Headshot style presets
HEADSHOT_STYLES = {
    "corporate": {
        "bg_color": (240, 240, 240),
        "face_strength": 0.6,
        "brightness": 10,
        "contrast": 5,
        "description": "Clean corporate headshot on light gray background",
    },
    "linkedin": {
        "bg_color": (230, 235, 245),
        "face_strength": 0.7,
        "brightness": 5,
        "contrast": 10,
        "description": "Professional LinkedIn profile photo",
    },
    "studio_classic": {
        "bg_color": (50, 50, 60),
        "face_strength": 0.8,
        "brightness": 0,
        "contrast": 15,
        "description": "Classic dark studio background",
    },
    "studio_gradient": {
        "bg_gradient": True,
        "bg_color_top": (80, 90, 110),
        "bg_color_bottom": (40, 45, 55),
        "face_strength": 0.75,
        "brightness": 5,
        "contrast": 10,
        "description": "Studio with gradient background",
    },
    "creative": {
        "bg_color": (255, 255, 255),
        "face_strength": 0.5,
        "brightness": 15,
        "contrast": -5,
        "description": "Bright, airy creative professional look",
    },
}


class HeadshotGeneratorPlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="headshot_generator",
            display_name="AI Headshot Generator",
            description="Generate professional headshots from casual photos. Corporate, LinkedIn, and studio styles.",
            icon="👔",
            category="creative",
            required_models=["rembg", "gfpgan"],
            estimated_vram_mb=800,
            supports_batch=True,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "style": {
                    "type": "string",
                    "enum": list(HEADSHOT_STYLES.keys()),
                    "default": "corporate",
                    "title": "Headshot Style",
                    "description": "Professional headshot style preset",
                },
                "face_strength": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7,
                    "title": "Face Enhancement Strength",
                    "description": "How much to enhance the face",
                },
                "custom_bg_path": {
                    "type": "string",
                    "default": "",
                    "title": "Custom Background",
                    "description": "Path to custom background image",
                },
                "crop_to_headshot": {
                    "type": "boolean",
                    "default": True,
                    "title": "Crop to Headshot",
                    "description": "Auto-crop to head and shoulders",
                },
                "output_size": {
                    "type": "string",
                    "enum": ["800x800", "1024x1024", "1200x1500", "original"],
                    "default": "1024x1024",
                    "title": "Output Size",
                    "description": "Final image dimensions",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        # Uses rembg and gfpgan which are registered by other plugins
        pass

    def _create_gradient_bg(self, size, color_top, color_bottom):
        """Create a gradient background."""
        w, h = size
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            ratio = y / h
            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
            gradient[y, :] = [r, g, b]
        return Image.fromarray(gradient)

    def process(self, input_paths: list[str], params: dict, progress_cb) -> list[str]:
        from rembg import remove as rembg_remove
        from PIL import ImageEnhance
        import cv2

        style_name = params.get("style", "corporate")
        style = HEADSHOT_STYLES.get(style_name, HEADSHOT_STYLES["corporate"])
        face_strength = params.get("face_strength", style.get("face_strength", 0.7))
        custom_bg = params.get("custom_bg_path", "")
        output_size_str = params.get("output_size", "1024x1024")

        mm = get_model_manager()
        outputs = []
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            try:
                # Step 1: Face Enhancement
                progress_cb((i / total) * 100 + 5, f"Enhancing face {i + 1}/{total}...")

                img_cv = load_image_cv2(path)
                if img_cv.shape[2] == 4:
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGRA2BGR)

                gfpgan = mm.load_sync("gfpgan")
                _, _, restored = gfpgan.enhance(
                    img_cv,
                    has_aligned=False,
                    only_center_face=False,
                    paste_back=True,
                )

                # Blend with original
                if face_strength < 1.0:
                    if img_cv.shape != restored.shape:
                        img_cv = cv2.resize(img_cv, (restored.shape[1], restored.shape[0]))
                    restored = cv2.addWeighted(
                        restored, face_strength, img_cv, 1 - face_strength, 0
                    )

                enhanced_pil = cv2_to_pil(restored)

                # Step 2: Background Removal
                progress_cb((i / total) * 100 + 30, f"Removing background {i + 1}/{total}...")
                rgba = rembg_remove(enhanced_pil.convert("RGBA"))

                # Step 3: Background Replacement
                progress_cb((i / total) * 100 + 50, f"Applying background {i + 1}/{total}...")

                if custom_bg and os.path.exists(custom_bg):
                    bg_img = Image.open(custom_bg)
                    result = composite_on_background(rgba, background_image=bg_img)
                elif style.get("bg_gradient"):
                    bg_img = self._create_gradient_bg(
                        rgba.size,
                        style.get("bg_color_top", (80, 90, 110)),
                        style.get("bg_color_bottom", (40, 45, 55)),
                    )
                    result = composite_on_background(rgba, background_image=bg_img)
                else:
                    result = composite_on_background(rgba, background_color=style["bg_color"])

                # Step 4: Color adjustments
                progress_cb((i / total) * 100 + 70, f"Applying style {i + 1}/{total}...")

                brightness = style.get("brightness", 0)
                if brightness != 0:
                    result = ImageEnhance.Brightness(result).enhance(1 + brightness / 50.0)

                contrast = style.get("contrast", 0)
                if contrast != 0:
                    result = ImageEnhance.Contrast(result).enhance(1 + contrast / 50.0)

                # Step 5: Resize to output
                if output_size_str != "original":
                    parts = output_size_str.split("x")
                    target_w, target_h = int(parts[0]), int(parts[1])
                    result = result.resize((target_w, target_h), Image.LANCZOS)

                output_path = self.get_output_path(path, f"_headshot_{style_name}")
                save_image_pil(result, output_path)
                outputs.append(output_path)

            except Exception as e:
                logger.error("Headshot generation failed for %s: %s", path, e)
                raise

        progress_cb(100, "Headshot generation complete")
        return outputs
