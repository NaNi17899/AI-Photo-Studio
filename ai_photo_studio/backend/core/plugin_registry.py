"""
Plugin registry — discovers and manages all AI feature plugins.
"""

import logging
from typing import Optional

from backend.core.plugin_base import PluginBase
from backend.core.model_manager import get_model_manager

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for all AI processing plugins.
    Handles discovery, registration, and access.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins = {}
        return cls._instance

    def register(self, plugin: PluginBase):
        """Register a plugin instance."""
        info = plugin.get_info()
        self._plugins[info.name] = plugin
        # Register the plugin's models with the model manager
        plugin.register_models(get_model_manager())
        logger.info("Registered plugin: %s (%s)", info.display_name, info.name)

    def get(self, name: str) -> Optional[PluginBase]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_all(self) -> dict[str, PluginBase]:
        """Get all registered plugins."""
        return dict(self._plugins)

    def get_info_all(self) -> list[dict]:
        """Get metadata for all plugins (for API responses)."""
        result = []
        for name, plugin in self._plugins.items():
            info = plugin.get_info()
            result.append(
                {
                    "name": info.name,
                    "display_name": info.display_name,
                    "description": info.description,
                    "icon": info.icon,
                    "category": info.category,
                    "supports_batch": info.supports_batch,
                    "estimated_vram_mb": info.estimated_vram_mb,
                    "params_schema": plugin.get_params_schema(),
                }
            )
        return result


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry singleton."""
    return PluginRegistry()


def discover_and_register_plugins():
    """
    Import and register all built-in plugins.
    Called once at application startup.
    """
    registry = get_plugin_registry()

    # Import each plugin module — they self-register
    from backend.plugins.background_removal.plugin import BackgroundRemovalPlugin
    from backend.plugins.face_enhancement.plugin import FaceEnhancementPlugin
    from backend.plugins.upscaling.plugin import UpscalingPlugin
    from backend.plugins.object_removal.plugin import ObjectRemovalPlugin
    from backend.plugins.watermark_removal.plugin import WatermarkRemovalPlugin
    from backend.plugins.color_grading.plugin import ColorGradingPlugin
    from backend.plugins.style_transfer.plugin import StyleTransferPlugin
    from backend.plugins.cartoon_anime.plugin import CartoonAnimePlugin
    from backend.plugins.headshot_generator.plugin import HeadshotGeneratorPlugin
    from backend.plugins.wedding_studio.plugin import WeddingStudioPlugin

    plugins = [
        BackgroundRemovalPlugin(),
        FaceEnhancementPlugin(),
        UpscalingPlugin(),
        ObjectRemovalPlugin(),
        WatermarkRemovalPlugin(),
        ColorGradingPlugin(),
        StyleTransferPlugin(),
        CartoonAnimePlugin(),
        HeadshotGeneratorPlugin(),
        WeddingStudioPlugin(),
    ]

    registered = 0
    for plugin in plugins:
        try:
            registry.register(plugin)
            registered += 1
        except Exception as e:
            name = plugin.get_info().name
            logger.warning("Plugin '%s' registration failed (missing deps?): %s", name, e)

    logger.info("Registered %d/%d plugins", registered, len(plugins))
