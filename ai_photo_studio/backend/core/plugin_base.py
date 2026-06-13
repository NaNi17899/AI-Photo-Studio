"""
Abstract plugin base class.
All AI feature modules must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Callable
from dataclasses import dataclass, field


@dataclass
class PluginInfo:
    """Plugin metadata."""

    name: str
    display_name: str
    description: str
    icon: str = "🔧"  # Emoji icon for UI
    category: str = "general"
    required_models: list[str] = field(default_factory=list)
    estimated_vram_mb: int = 0
    supports_batch: bool = True
    version: str = "1.0.0"


class PluginBase(ABC):
    """
    Base class for all AI processing plugins.

    Each plugin must:
    1. Define its metadata via get_info()
    2. Declare parameter schema via get_params_schema()
    3. Register required models via register_models()
    4. Implement the process() method
    """

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Return plugin metadata."""
        ...

    @abstractmethod
    def get_params_schema(self) -> dict:
        """
        Return JSON Schema for the plugin's parameters.
        Used by the frontend to render controls.

        Example:
            {
                "type": "object",
                "properties": {
                    "strength": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.5,
                        "title": "Restoration Strength",
                        "description": "How strongly to apply restoration"
                    }
                }
            }
        """
        ...

    @abstractmethod
    def register_models(self, model_manager) -> None:
        """
        Register all required models with the ModelManager.
        Called once at startup.
        """
        ...

    @abstractmethod
    def process(
        self, input_paths: list[str], params: dict, progress_cb: Callable[[float, str], None]
    ) -> list[str]:
        """
        Process one or more images.

        Args:
            input_paths: List of input file paths
            params: Processing parameters matching the schema
            progress_cb: Callback function(percent, message) for progress updates

        Returns:
            List of output file paths
        """
        ...

    def validate_params(self, params: dict) -> dict:
        """
        Validate and fill in defaults for parameters.
        Override for custom validation.
        """
        schema = self.get_params_schema()
        props = schema.get("properties", {})
        validated = {}
        for key, spec in props.items():
            if key in params:
                validated[key] = params[key]
            elif "default" in spec:
                validated[key] = spec["default"]
        return validated

    def get_output_path(self, input_path: str, suffix: str = "") -> str:
        """Generate an output path from an input path."""
        import os
        import time
        from backend.config import get_settings

        settings = get_settings()
        basename = os.path.splitext(os.path.basename(input_path))[0]
        plugin_name = self.get_info().name
        timestamp = int(time.time())
        filename = f"{basename}_{plugin_name}{suffix}_{timestamp}.png"
        return str(settings.storage.outputs_dir / filename)
