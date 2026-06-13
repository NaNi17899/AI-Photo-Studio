import os
import urllib.request

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def download(url, dest, name):
    if os.path.exists(dest):
        print(f"  SKIP  {name} already downloaded")
        return
    print(f"  DOWNLOADING  {name}...")
    print(f"  From: {url}")

    def progress(count, block, total):
        if total > 0:
            pct = int(count * block * 100 / total)
            mb_done = count * block / 1024**2
            mb_total = total / 1024**2
            print(f"\r  {pct}%  {mb_done:.1f}/{mb_total:.1f} MB", end="", flush=True)

    try:
        urllib.request.urlretrieve(url, dest, progress)
        print(f"\n  DONE  Saved to {dest}")
    except Exception as e:
        print(f"\n  ERROR  {e}")
        print(f"  Manual download: {url}")


print("=" * 55)
print(" AI Photo Studio - Downloading Models")
print("=" * 55)

print("\n[1/3] GFPGAN v1.4 (face enhancement, ~350MB)...")
download(
    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth",
    os.path.join(MODELS_DIR, "GFPGANv1.4.pth"),
    "GFPGANv1.4.pth",
)

print("\n[2/3] Real-ESRGAN x4plus (upscaling, ~67MB)...")
download(
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    os.path.join(MODELS_DIR, "RealESRGAN_x4plus.pth"),
    "RealESRGAN_x4plus.pth",
)

print("\n[3/3] Real-ESRGAN x4plus face (face upscaling, ~67MB)...")
download(
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGANv0.2.2.4_x4plus_anime_6B.pth",
    os.path.join(MODELS_DIR, "RealESRGANv0.2.2.4_anime.pth"),
    "RealESRGAN anime model",
)

print("\n" + "=" * 55)
print(" rembg downloads its model automatically on first run")
print(" LaMa downloads automatically on first run")
print("=" * 55)
print("\n All models ready. Run: python step4_test_models.py")
