"""
Wedding Studio Workflow Plugin.
Batch pipeline orchestrator that chains color grading, face enhancement,
and upscaling for consistent wedding album processing.
"""

import logging

from backend.core.plugin_base import PluginBase, PluginInfo
from backend.core.plugin_registry import get_plugin_registry


logger = logging.getLogger(__name__)


# Wedding workflow presets
WEDDING_WORKFLOWS = {
    "classic_romantic": {
        "description": "Soft, warm, romantic feel with gentle face enhancement",
        "steps": [
            {"plugin": "color_grading", "params": {"preset": "wedding_classic"}},
            {
                "plugin": "face_enhancement",
                "params": {"model": "gfpgan", "strength": 0.5, "upscale": 1},
            },
        ],
    },
    "moody_dramatic": {
        "description": "Dark, dramatic mood with rich contrast",
        "steps": [
            {"plugin": "color_grading", "params": {"preset": "moody_wedding"}},
            {
                "plugin": "face_enhancement",
                "params": {"model": "gfpgan", "strength": 0.6, "upscale": 1},
            },
        ],
    },
    "bright_airy": {
        "description": "Light, bright, and airy with pastel tones",
        "steps": [
            {
                "plugin": "color_grading",
                "params": {
                    "brightness": 15,
                    "contrast": -10,
                    "saturation": -10,
                    "temperature": 5,
                    "pastel_strength": 25,
                    "fade": 10,
                },
            },
            {
                "plugin": "face_enhancement",
                "params": {"model": "gfpgan", "strength": 0.4, "upscale": 1},
            },
        ],
    },
    "golden_sunset": {
        "description": "Warm golden tones, great for outdoor ceremonies",
        "steps": [
            {"plugin": "color_grading", "params": {"preset": "golden_hour"}},
            {
                "plugin": "face_enhancement",
                "params": {"model": "gfpgan", "strength": 0.5, "upscale": 1},
            },
        ],
    },
    "full_retouching": {
        "description": "Complete retouch: color grade + face enhance + upscale",
        "steps": [
            {"plugin": "color_grading", "params": {"preset": "wedding_classic"}},
            {
                "plugin": "face_enhancement",
                "params": {"model": "gfpgan", "strength": 0.6, "upscale": 1},
            },
            {"plugin": "upscaling", "params": {"scale": 2, "face_enhance": True}},
        ],
    },
}


class WeddingStudioPlugin(PluginBase):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="wedding_studio",
            display_name="Wedding Studio",
            description="Batch wedding album processing with consistent styling. Chains color grading + face enhancement + upscaling.",
            icon="💒",
            category="workflow",
            required_models=[],
            estimated_vram_mb=500,
            supports_batch=True,
        )

    def get_params_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "enum": list(WEDDING_WORKFLOWS.keys()),
                    "default": "classic_romantic",
                    "title": "Workflow Preset",
                    "description": "Predefined wedding editing workflow",
                },
                "custom_steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "plugin": {"type": "string"},
                            "params": {"type": "object"},
                        },
                    },
                    "default": [],
                    "title": "Custom Steps",
                    "description": "Override with custom workflow steps",
                },
                "apply_to_all": {
                    "type": "boolean",
                    "default": True,
                    "title": "Consistent Style",
                    "description": "Apply identical settings to all images",
                },
            },
        }

    def register_models(self, model_manager) -> None:
        # Uses models from other plugins (color_grading, face_enhancement, upscaling)
        pass

    def process(self, input_paths: list[str], params: dict, progress_cb) -> list[str]:

        workflow_name = params.get("workflow", "classic_romantic")
        custom_steps = params.get("custom_steps", [])

        # Determine steps
        if custom_steps:
            steps = custom_steps
        else:
            workflow = WEDDING_WORKFLOWS.get(workflow_name, WEDDING_WORKFLOWS["classic_romantic"])
            steps = workflow["steps"]

        registry = get_plugin_registry()
        total_images = len(input_paths)
        total_steps = len(steps)
        outputs = []

        for img_idx, path in enumerate(input_paths):
            try:
                current_paths = [path]

                for step_idx, step in enumerate(steps):
                    plugin_name = step["plugin"]
                    step_params = step.get("params", {})

                    plugin = registry.get(plugin_name)
                    if not plugin:
                        logger.warning("Plugin '%s' not found, skipping step", plugin_name)
                        continue

                    overall_progress = (
                        (img_idx * total_steps + step_idx) / (total_images * total_steps)
                    ) * 100
                    progress_cb(
                        overall_progress,
                        f"Image {img_idx + 1}/{total_images} — Step {step_idx + 1}/{total_steps}: {plugin_name}",
                    )

                    # Process with this plugin
                    step_outputs = plugin.process(
                        current_paths,
                        plugin.validate_params(step_params),
                        lambda p, m="": None,  # Sub-plugin progress ignored
                    )

                    # Output of this step becomes input of next step
                    current_paths = step_outputs

                # Final output is the result of the last step
                if current_paths:
                    outputs.extend(current_paths)

            except Exception as e:
                logger.error("Wedding workflow failed for %s: %s", path, e)
                raise

        progress_cb(100, f"Wedding workflow complete — processed {total_images} images")
        return outputs
