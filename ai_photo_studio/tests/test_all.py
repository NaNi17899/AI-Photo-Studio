"""
Test suite for AI Photo Studio.
Run: python -m pytest tests/ -v
"""

import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfig:
    """Test configuration module."""

    def test_settings_creation(self):
        from backend.config import get_settings

        settings = get_settings()
        assert settings.app_name == "AI Photo Studio"
        assert settings.version == "2.0.0"
        assert settings.gpu.max_vram_usage_mb > 0
        assert settings.server.port == 8000

    def test_storage_dirs_created(self):
        from backend.config import get_settings

        settings = get_settings()
        settings.storage.ensure_dirs()
        assert settings.storage.uploads_dir.exists()
        assert settings.storage.outputs_dir.exists()
        assert settings.storage.models_dir.exists()

    def test_model_registry(self):
        from backend.config import MODEL_REGISTRY

        assert "gfpgan_v1.4" in MODEL_REGISTRY
        assert "realesrgan_x4plus" in MODEL_REGISTRY
        assert MODEL_REGISTRY["gfpgan_v1.4"].required is True


class TestGPUUtils:
    """Test GPU utility functions."""

    def test_get_device(self):
        from backend.core.gpu_utils import get_device

        device = get_device("auto")
        assert device in ("cuda", "cpu")

    def test_get_device_cpu(self):
        from backend.core.gpu_utils import get_device

        assert get_device("cpu") == "cpu"

    def test_get_gpu_info(self):
        from backend.core.gpu_utils import get_gpu_info

        info = get_gpu_info()
        assert "cuda_available" in info
        assert "device_count" in info

    def test_optimal_dtype(self):
        from backend.core.gpu_utils import optimal_dtype
        import torch

        dtype = optimal_dtype(prefer_half=True)
        assert dtype in (torch.float16, torch.float32)


class TestModelManager:
    """Test the VRAM-aware model manager."""

    def test_singleton(self):
        from backend.core.model_manager import ModelManager

        mm1 = ModelManager()
        mm2 = ModelManager()
        assert mm1 is mm2

    def test_register_model(self):
        from backend.core.model_manager import get_model_manager

        mm = get_model_manager()
        mm.register("test_model", lambda: "test_loaded", vram_mb=100)
        assert "test_model" in mm._models

    def test_load_sync(self):
        from backend.core.model_manager import get_model_manager

        mm = get_model_manager()
        mm.register("test_sync", lambda: {"model": "loaded"}, vram_mb=10)
        result = mm.load_sync("test_sync")
        assert result == {"model": "loaded"}

    def test_unload_sync(self):
        from backend.core.model_manager import get_model_manager

        mm = get_model_manager()
        mm.register("test_unload", lambda: "data", vram_mb=10)
        mm.load_sync("test_unload")
        mm.unload_sync("test_unload")
        assert mm._models["test_unload"].model is None

    def test_get_status(self):
        from backend.core.model_manager import get_model_manager

        mm = get_model_manager()
        status = mm.get_status()
        assert isinstance(status, dict)


class TestJobQueue:
    """Test the async job queue."""

    def test_job_creation(self):
        from backend.core.job_queue import Job, JobStatus

        job = Job(plugin="test")
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0
        assert len(job.id) == 8

    def test_job_to_dict(self):
        from backend.core.job_queue import Job

        job = Job(plugin="background_removal")
        d = job.to_dict()
        assert d["plugin"] == "background_removal"
        assert d["status"] == "pending"
        assert "id" in d


class TestPluginRegistry:
    """Test plugin discovery and registration."""

    def test_registry_singleton(self):
        from backend.core.plugin_registry import PluginRegistry

        r1 = PluginRegistry()
        r2 = PluginRegistry()
        assert r1 is r2


class TestImageUtils:
    """Test image utility functions."""

    def test_create_thumbnail(self):
        from PIL import Image
        from backend.core.image_utils import create_thumbnail

        img = Image.new("RGB", (1000, 800), (255, 0, 0))
        thumb = create_thumbnail(img, (256, 256))
        assert max(thumb.size) <= 256

    def test_composite_on_background(self):
        from PIL import Image
        from backend.core.image_utils import composite_on_background

        fg = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        result = composite_on_background(fg, background_color=(0, 0, 255))
        assert result.mode == "RGB"
        assert result.size == (100, 100)

    def test_refine_mask_edges(self):
        import numpy as np
        from backend.core.image_utils import refine_mask_edges

        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[30:70, 30:70] = 255
        refined = refine_mask_edges(mask, blur_radius=3)
        assert refined.shape == (100, 100)


class TestColorGrading:
    """Test color grading functions."""

    def test_apply_temperature(self):
        import numpy as np
        from backend.plugins.color_grading.plugin import apply_temperature

        img = np.full((10, 10, 3), 128, dtype=np.uint8)
        warm = apply_temperature(img, 20)
        assert warm.shape == img.shape
        # Red channel should increase for warm temp
        assert warm[0, 0, 0] > img[0, 0, 0]

    def test_preset_exists(self):
        from backend.plugins.color_grading.plugin import PRESETS

        assert "golden_hour" in PRESETS
        assert "cinematic" in PRESETS
        assert "kdrama" in PRESETS
        assert "bollywood" in PRESETS
        assert "wedding_classic" in PRESETS


class TestAPI:
    """Test API endpoints using FastAPI TestClient."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.main import app

        return TestClient(app)

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_api_info(self, client):
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "AI Photo Studio"
        assert "plugins" in data

    def test_settings(self, client):
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0.0"

    def test_list_models(self, client):
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data

    def test_vram_status(self, client):
        response = client.get("/api/models/vram")
        assert response.status_code == 200

    def test_list_jobs(self, client):
        response = client.get("/api/jobs")
        assert response.status_code == 200

    def test_list_presets(self, client):
        response = client.get("/api/presets")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
