"""
Watermark & Text Removal Plugin.
Uses EasyOCR for text detection + LaMa for cleanup.
Supports automatic mask generation from detected text.
"""

import os
import logging
import numpy as np
from PIL import Image, ImageDraw

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.model_manager import get_model_manager
from backend.core.image_utils import load_image_pil, save_image_pil

logger = logging.getLogger(__name__)


class WatermarkRemovalPlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="watermark_removal",
            display_name="Watermark & Text Removal",
            description="Automatically detect and remove watermarks, text overlays, and logos using OCR + AI inpainting.",
            icon="🔤",
            category="editing",
            required_models=["lama"],
            estimated_vram_mb=400,
            supports_batch=True,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["auto_detect", "manual_mask"],
                    "default": "auto_detect",
                    "title": "Detection Mode",
                    "description": "Auto-detect text or use manual mask",
                },
                "mask_path": {
                    "type": "string",
                    "default": "",
                    "title": "Manual Mask Path",
                    "description": "Path to mask image for manual mode",
                },
                "mask_data": {
                    "type": "string",
                    "default": "",
                    "title": "Mask Data",
                    "description": "Base64 mask from canvas",
                },
                "languages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["en"],
                    "title": "OCR Languages",
                    "description": "Languages for text detection",
                },
                "mask_padding": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 50,
                    "default": 10,
                    "title": "Mask Padding",
                    "description": "Extra padding around detected text",
                },
                "confidence_threshold": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 1.0,
                    "default": 0.3,
                    "title": "Confidence Threshold",
                    "description": "Minimum OCR confidence to include text region",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        def load_lama():
            from simple_lama_inpainting import SimpleLama

            return SimpleLama()

        def load_easyocr():
            import easyocr

            reader = easyocr.Reader(["en"], gpu=True)
            return reader

        # LaMa may already be registered by object_removal, this is safe
        if "lama" not in model_manager._models:
            model_manager.register("lama", load_lama, vram_mb=300)
        model_manager.register("easyocr", load_easyocr, vram_mb=400)

    def _detect_text_regions(self, img: Image.Image, params: dict) -> Image.Image:
        """Use EasyOCR to detect text and generate a mask."""
        mm = get_model_manager()
        reader = mm.load_sync("easyocr")

        img_np = np.array(img.convert("RGB"))
        threshold = params.get("confidence_threshold", 0.3)
        padding = params.get("mask_padding", 10)

        # Detect text
        results = reader.readtext(img_np)

        # Create mask from detections
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)

        for bbox, text, conf in results:
            if conf >= threshold:
                # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                pts = np.array(bbox, dtype=np.int32)
                x_min = max(0, pts[:, 0].min() - padding)
                y_min = max(0, pts[:, 1].min() - padding)
                x_max = min(img.size[0], pts[:, 0].max() + padding)
                y_max = min(img.size[1], pts[:, 1].max() + padding)
                draw.rectangle([x_min, y_min, x_max, y_max], fill=255)
                logger.debug("Detected text: '%s' (conf=%.2f)", text, conf)

        return mask

    def process(self, input_paths: list[str], params: dict, progress_cb) -> list[str]:
        import base64
        from io import BytesIO

        mode = params.get("mode", "auto_detect")
        mm = get_model_manager()

        outputs = []
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            try:
                progress_cb((i / total) * 100, f"Processing {i + 1}/{total}...")

                img = load_image_pil(path).convert("RGB")

                # Get or generate mask
                if mode == "auto_detect":
                    progress_cb((i / total) * 100 + 10, "Detecting text regions...")
                    mask = self._detect_text_regions(img, params)

                    # Check if any text was detected
                    mask_np = np.array(mask)
                    if mask_np.max() == 0:
                        logger.info("No text detected in %s", path)
                        # Save original
                        output_path = self.get_output_path(path, "_clean")
                        save_image_pil(img, output_path)
                        outputs.append(output_path)
                        continue
                else:
                    # Manual mask
                    mask_data = params.get("mask_data", "")
                    mask_path = params.get("mask_path", "")
                    if mask_data:
                        mask_bytes = base64.b64decode(mask_data)
                        mask = Image.open(BytesIO(mask_bytes)).convert("L")
                    elif mask_path and os.path.exists(mask_path):
                        mask = Image.open(mask_path).convert("L")
                    else:
                        raise ValueError("No mask provided for manual mode")

                if mask.size != img.size:
                    mask = mask.resize(img.size, Image.NEAREST)

                # Run LaMa inpainting
                progress_cb((i / total) * 100 + 50, "Removing watermark...")
                lama = mm.load_sync("lama")
                result = lama(img, mask)

                output_path = self.get_output_path(path, "_clean")
                save_image_pil(result, output_path)
                outputs.append(output_path)

            except Exception as e:
                logger.error("Watermark removal failed for %s: %s", path, e)
                raise

        progress_cb(100, "Watermark removal complete")
        return outputs
