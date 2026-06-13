"""
Image Upscaling Plugin.
Uses Real-ESRGAN for 2x, 4x, and 8x upscaling with face-aware enhancement.
Tile-based processing for large images to avoid OOM.
"""

import os
import logging
import cv2

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.model_manager import get_model_manager
from backend.core.image_utils import load_image_cv2, save_image_cv2
from backend.core.gpu_utils import cpu_fallback
from backend.config import get_settings

logger = logging.getLogger(__name__)


class UpscalingPlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="upscaling",
            display_name="Image Upscaling",
            description="Upscale images 2x, 4x, or 8x using Real-ESRGAN with optional face enhancement.",
            icon="🔍",
            category="enhancement",
            required_models=["realesrgan"],
            estimated_vram_mb=400,
            supports_batch=True,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "scale": {
                    "type": "integer",
                    "enum": [2, 4, 8],
                    "default": 4,
                    "title": "Scale Factor",
                    "description": "Upscaling factor (8x = two passes of 4x)",
                },
                "model_type": {
                    "type": "string",
                    "enum": ["general", "anime"],
                    "default": "general",
                    "title": "Model Type",
                    "description": "General for photos, Anime for illustrations",
                },
                "face_enhance": {
                    "type": "boolean",
                    "default": False,
                    "title": "Face Enhancement",
                    "description": "Apply GFPGAN face enhancement after upscaling",
                },
                "tile_size": {
                    "type": "integer",
                    "minimum": 128,
                    "maximum": 512,
                    "default": 256,
                    "title": "Tile Size",
                    "description": "Processing tile size (lower = less VRAM, slower)",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        settings = get_settings()
        models_dir = settings.storage.models_dir

        def load_realesrgan_x4():
            import torch
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer

            model = RRDBNet(
                num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4
            )
            return RealESRGANer(
                scale=4,
                model_path=str(models_dir / "RealESRGAN_x4plus.pth"),
                model=model,
                tile=256,
                tile_pad=10,
                pre_pad=0,
                half=torch.cuda.is_available(),
            )

        def load_realesrgan_anime():
            import torch
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer

            model = RRDBNet(
                num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4
            )
            anime_path = str(models_dir / "RealESRGAN_x4plus_anime_6B.pth")
            if not os.path.exists(anime_path):
                # Fall back to general model
                return load_realesrgan_x4()
            return RealESRGANer(
                scale=4,
                model_path=anime_path,
                model=model,
                tile=256,
                tile_pad=10,
                pre_pad=0,
                half=torch.cuda.is_available(),
            )

        model_manager.register("realesrgan", load_realesrgan_x4, vram_mb=400)
        model_manager.register("realesrgan_anime", load_realesrgan_anime, vram_mb=300)

    @cpu_fallback
    def process(
        self, input_paths: list[str], params: dict, progress_cb, _force_cpu: bool = False
    ) -> list[str]:

        scale = params.get("scale", 4)
        model_type = params.get("model_type", "general")
        face_enhance = params.get("face_enhance", False)
        tile_size = params.get("tile_size", 256)

        mm = get_model_manager()
        model_name = "realesrgan" if model_type == "general" else "realesrgan_anime"
        upsampler = mm.load_sync(model_name)
        upsampler.tile = tile_size

        outputs = []
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            try:
                progress_cb((i / total) * 100, f"Upscaling image {i + 1}/{total}...")

                img_cv = load_image_cv2(path)
                if img_cv.shape[2] == 4:
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGRA2BGR)

                h, w = img_cv.shape[:2]

                if scale <= 4:
                    # Single pass
                    output, _ = upsampler.enhance(img_cv, outscale=scale)
                else:
                    # 8x: two passes of 4x, then downscale to exact 8x
                    progress_cb((i / total) * 100, f"Upscaling {i + 1}/{total} (pass 1/2)...")
                    output_4x, _ = upsampler.enhance(img_cv, outscale=4)
                    progress_cb(
                        ((i + 0.5) / total) * 100, f"Upscaling {i + 1}/{total} (pass 2/2)..."
                    )
                    output, _ = upsampler.enhance(output_4x, outscale=2)

                # Face enhancement post-processing
                if face_enhance:
                    try:
                        progress_cb(
                            ((i + 0.8) / total) * 100, f"Enhancing faces {i + 1}/{total}..."
                        )
                        gfpgan = mm.load_sync("gfpgan")
                        _, _, output = gfpgan.enhance(
                            output, has_aligned=False, only_center_face=False, paste_back=True
                        )
                    except Exception as e:
                        logger.warning("Face enhancement after upscale failed: %s", e)

                nh, nw = output.shape[:2]
                output_path = self.get_output_path(path, f"_x{scale}")
                save_image_cv2(output, output_path)
                outputs.append(output_path)
                logger.info("Upscaled %dx%d -> %dx%d", w, h, nw, nh)

            except Exception as e:
                logger.error("Upscaling failed for %s: %s", path, e)
                raise

        progress_cb(100, "Upscaling complete")
        return outputs
