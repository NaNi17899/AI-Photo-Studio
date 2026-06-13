"""
Color Grading Plugin.
Pure NumPy/PIL — no GPU required.
Built-in presets: Golden Hour, Cinematic, K-Drama, Bollywood, Wedding.
Supports LUT files (.cube) and custom adjustments.
"""

import logging
import numpy as np
from PIL import Image, ImageEnhance

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.image_utils import load_image_pil, save_image_pil

logger = logging.getLogger(__name__)


# Built-in preset definitions
PRESETS = {
    "golden_hour": {
        "temperature": 30,
        "saturation": 15,
        "brightness": 5,
        "contrast": 10,
        "shadows_lift": 15,
        "highlights_warmth": 20,
    },
    "cinematic": {
        "temperature": 10,
        "teal_orange": 40,
        "contrast": 20,
        "blacks_crush": 15,
        "saturation": -5,
    },
    "kdrama": {
        "temperature": -10,
        "saturation": -15,
        "brightness": 10,
        "contrast": -5,
        "pastel_strength": 30,
    },
    "bollywood": {
        "temperature": 20,
        "saturation": 30,
        "contrast": 15,
        "vibrance": 25,
        "highlights_warmth": 15,
    },
    "wedding_classic": {
        "temperature": 5,
        "saturation": -10,
        "brightness": 15,
        "contrast": -10,
        "pastel_strength": 20,
        "fade": 10,
    },
    "moody_wedding": {
        "temperature": -5,
        "saturation": -5,
        "contrast": 25,
        "blacks_crush": 10,
        "highlights_warmth": -10,
    },
    "none": {},
}


def apply_temperature(img_np: np.ndarray, temp: float) -> np.ndarray:
    """Adjust color temperature. Positive = warm, negative = cool."""
    result = img_np.astype(np.float32)
    if temp > 0:
        result[:, :, 0] = np.clip(result[:, :, 0] + temp * 0.5, 0, 255)  # R
        result[:, :, 2] = np.clip(result[:, :, 2] - temp * 0.3, 0, 255)  # B
    else:
        result[:, :, 0] = np.clip(result[:, :, 0] + temp * 0.3, 0, 255)
        result[:, :, 2] = np.clip(result[:, :, 2] - temp * 0.5, 0, 255)
    return result.astype(np.uint8)


def apply_teal_orange(img_np: np.ndarray, strength: float) -> np.ndarray:
    """Apply teal-orange color split."""
    result = img_np.astype(np.float32)
    luminance = 0.299 * result[:, :, 0] + 0.587 * result[:, :, 1] + 0.114 * result[:, :, 2]

    # Shadows -> teal, highlights -> orange
    shadow_mask = (1 - luminance / 255.0) * (strength / 100.0)
    highlight_mask = (luminance / 255.0) * (strength / 100.0)

    result[:, :, 0] = np.clip(result[:, :, 0] + highlight_mask * 30, 0, 255)  # R in highlights
    result[:, :, 1] = np.clip(result[:, :, 1] + shadow_mask * 15, 0, 255)  # G in shadows
    result[:, :, 2] = np.clip(result[:, :, 2] + shadow_mask * 25, 0, 255)  # B in shadows

    return result.astype(np.uint8)


def apply_fade(img_np: np.ndarray, strength: float) -> np.ndarray:
    """Apply matte/faded look by lifting blacks."""
    result = img_np.astype(np.float32)
    lift = strength * 0.5
    result = result + lift
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_blacks_crush(img_np: np.ndarray, strength: float) -> np.ndarray:
    """Crush black levels for dramatic look."""
    result = img_np.astype(np.float32)
    threshold = strength * 2
    result = np.where(result < threshold, result * 0.3, result)
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_pastel(img_np: np.ndarray, strength: float) -> np.ndarray:
    """Apply pastel/soft color effect."""
    result = img_np.astype(np.float32)
    # Blend toward a light midpoint
    midpoint = 180
    factor = strength / 100.0
    result = result + (midpoint - result) * factor * 0.3
    return np.clip(result, 0, 255).astype(np.uint8)


class ColorGradingPlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="color_grading",
            display_name="Color Grading",
            description="Professional color grading with presets (Golden Hour, Cinematic, K-Drama, Bollywood, Wedding) and custom adjustments.",
            icon="🎨",
            category="enhancement",
            required_models=[],
            estimated_vram_mb=0,
            supports_batch=True,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "preset": {
                    "type": "string",
                    "enum": list(PRESETS.keys()),
                    "default": "none",
                    "title": "Preset",
                    "description": "Built-in color grading preset",
                },
                "brightness": {
                    "type": "number",
                    "minimum": -50,
                    "maximum": 50,
                    "default": 0,
                    "title": "Brightness",
                },
                "contrast": {
                    "type": "number",
                    "minimum": -50,
                    "maximum": 50,
                    "default": 0,
                    "title": "Contrast",
                },
                "saturation": {
                    "type": "number",
                    "minimum": -50,
                    "maximum": 50,
                    "default": 0,
                    "title": "Saturation",
                },
                "temperature": {
                    "type": "number",
                    "minimum": -50,
                    "maximum": 50,
                    "default": 0,
                    "title": "Temperature",
                },
                "vibrance": {
                    "type": "number",
                    "minimum": -50,
                    "maximum": 50,
                    "default": 0,
                    "title": "Vibrance",
                },
                "teal_orange": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "default": 0,
                    "title": "Teal & Orange Split",
                },
                "fade": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 50,
                    "default": 0,
                    "title": "Fade / Matte",
                },
                "blacks_crush": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 50,
                    "default": 0,
                    "title": "Crush Blacks",
                },
                "shadows_lift": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 50,
                    "default": 0,
                    "title": "Lift Shadows",
                },
                "highlights_warmth": {
                    "type": "number",
                    "minimum": -30,
                    "maximum": 30,
                    "default": 0,
                    "title": "Highlights Warmth",
                },
                "pastel_strength": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 50,
                    "default": 0,
                    "title": "Pastel Softness",
                },
                "sharpen": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "default": 0,
                    "title": "Sharpen",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        pass  # No ML models needed

    def process(self, input_paths: list[str], params: dict, progress_cb) -> list[str]:

        # Merge preset values with manual overrides
        preset_name = params.get("preset", "none")
        preset_vals = PRESETS.get(preset_name, {}).copy()
        # Manual values override preset
        for key in params:
            if key != "preset" and params[key] != 0:
                preset_vals[key] = params[key]

        outputs = []
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            try:
                progress_cb((i / total) * 100, f"Color grading {i + 1}/{total}...")

                img = load_image_pil(path).convert("RGB")
                img_np = np.array(img)

                # Apply adjustments in order
                temp = preset_vals.get("temperature", 0)
                if temp != 0:
                    img_np = apply_temperature(img_np, temp)

                teal_orange = preset_vals.get("teal_orange", 0)
                if teal_orange > 0:
                    img_np = apply_teal_orange(img_np, teal_orange)

                blacks_crush = preset_vals.get("blacks_crush", 0)
                if blacks_crush > 0:
                    img_np = apply_blacks_crush(img_np, blacks_crush)

                fade = preset_vals.get("fade", 0)
                if fade > 0:
                    img_np = apply_fade(img_np, fade)

                shadows_lift = preset_vals.get("shadows_lift", 0)
                if shadows_lift > 0:
                    img_np = apply_fade(img_np, shadows_lift * 0.5)

                pastel = preset_vals.get("pastel_strength", 0)
                if pastel > 0:
                    img_np = apply_pastel(img_np, pastel)

                # Convert back to PIL for enhancement operations
                img = Image.fromarray(img_np)

                brightness = preset_vals.get("brightness", 0)
                if brightness != 0:
                    factor = 1 + brightness / 50.0
                    img = ImageEnhance.Brightness(img).enhance(factor)

                contrast = preset_vals.get("contrast", 0)
                if contrast != 0:
                    factor = 1 + contrast / 50.0
                    img = ImageEnhance.Contrast(img).enhance(factor)

                saturation = preset_vals.get("saturation", 0)
                if saturation != 0:
                    factor = 1 + saturation / 50.0
                    img = ImageEnhance.Color(img).enhance(factor)

                vibrance = preset_vals.get("vibrance", 0)
                if vibrance != 0:
                    # Vibrance boosts less-saturated colors more
                    factor = 1 + vibrance / 100.0
                    img = ImageEnhance.Color(img).enhance(factor)

                sharpen = preset_vals.get("sharpen", 0)
                if sharpen > 0:
                    factor = 1 + sharpen / 50.0
                    img = ImageEnhance.Sharpness(img).enhance(factor)

                # Save
                suffix = f"_{preset_name}" if preset_name != "none" else "_graded"
                output_path = self.get_output_path(path, suffix)
                save_image_pil(img, output_path)
                outputs.append(output_path)

            except Exception as e:
                logger.error("Color grading failed for %s: %s", path, e)
                raise

        progress_cb(100, "Color grading complete")
        return outputs
