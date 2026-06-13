"""
Model Download Script — downloads all required AI model weights.
Run: python scripts/download_models.py
"""

import os
import sys
import urllib.request

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings, MODEL_REGISTRY


def download_with_progress(url: str, dest: str, name: str):
    """Download a file with progress bar."""
    if os.path.exists(dest):
        size_mb = os.path.getsize(dest) / 1024**2
        print(f"  ✅ SKIP  {name} ({size_mb:.0f} MB) — already downloaded")
        return True

    print(f"  ⬇  DOWNLOADING  {name}")
    print(f"     From: {url}")

    def progress(count, block_size, total_size):
        if total_size > 0:
            pct = min(100, int(count * block_size * 100 / total_size))
            done_mb = count * block_size / 1024**2
            total_mb = total_size / 1024**2
            bar = "█" * (pct // 3) + "░" * (33 - pct // 3)
            print(f"\r     [{bar}] {pct}%  {done_mb:.1f}/{total_mb:.1f} MB", end="", flush=True)

    try:
        urllib.request.urlretrieve(url, dest, progress)
        print(f"\n     ✅ Saved to {dest}")
        return True
    except Exception as e:
        print(f"\n     ❌ ERROR: {e}")
        print(f"     Manual download: {url}")
        if os.path.exists(dest):
            os.remove(dest)
        return False


def main():
    settings = get_settings()
    models_dir = settings.storage.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  AI Photo Studio — Model Downloader")
    print("=" * 60)

    # Core models (required)
    print("\n📦 Core Models (required):")
    core_models = {k: v for k, v in MODEL_REGISTRY.items() if v.required}
    for name, entry in core_models.items():
        dest = str(models_dir / entry.filename)
        download_with_progress(entry.url, dest, f"{name} ({entry.description})")

    # Optional models
    print("\n📦 Optional Models:")
    optional_models = {k: v for k, v in MODEL_REGISTRY.items() if not v.required}
    for name, entry in optional_models.items():
        dest = str(models_dir / entry.filename)
        download_with_progress(entry.url, dest, f"{name} ({entry.description})")

    # Auto-download models (rembg, LaMa download automatically)
    print("\n📦 Auto-download models:")
    print("  ℹ  rembg (U2NET) — downloads automatically on first use")
    print("  ℹ  LaMa — downloads automatically on first use")
    print("  ℹ  EasyOCR — downloads automatically on first use")
    print("  ℹ  Stable Diffusion 1.5 — downloads from HuggingFace on first use (~4GB)")

    # Summary
    print("\n" + "=" * 60)
    total_downloaded = sum(
        1 for entry in MODEL_REGISTRY.values() if (models_dir / entry.filename).exists()
    )
    print(f"  {total_downloaded}/{len(MODEL_REGISTRY)} models downloaded")
    print(f"  Models directory: {models_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
