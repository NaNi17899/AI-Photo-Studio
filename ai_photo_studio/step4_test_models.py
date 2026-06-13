import os
import time
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)


def make_test_image():
    img = Image.new("RGB", (400, 400), (135, 180, 220))
    draw = ImageDraw.Draw(img)
    draw.ellipse([120, 60, 280, 200], fill=(255, 220, 180))
    draw.rectangle([140, 200, 260, 360], fill=(70, 130, 180))
    draw.ellipse([115, 55, 285, 205], outline=(80, 60, 40), width=2)
    path = os.path.join(BASE_DIR, "temp", "test_input.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


results = []

print("=" * 55)
print(" AI Photo Studio - Testing All Models")
print("=" * 55)

test_img_path = make_test_image()
print(f"\n Test image created: {test_img_path}")

print("\n[TEST 1] Background Removal (rembg)...")
try:
    from rembg import remove

    img = Image.open(test_img_path)
    t = time.time()
    out = remove(img)
    elapsed = time.time() - t
    out_path = os.path.join(OUTPUTS_DIR, "test_bg_removed.png")
    out.save(out_path)
    print(f"  PASS  Background removed in {elapsed:.1f}s")
    print(f"  Saved: {out_path}")
    results.append(("Background Removal", True, f"{elapsed:.1f}s"))
except Exception as e:
    print(f"  FAIL  {e}")
    results.append(("Background Removal", False, str(e)[:60]))

print("\n[TEST 2] Face Enhancement (GFPGAN)...")
try:
    import cv2
    import torch
    from gfpgan import GFPGANer

    model_path = os.path.join(MODELS_DIR, "GFPGANv1.4.pth")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path} - run step3 first")
    restorer = GFPGANer(
        model_path=model_path, upscale=2, arch="clean", channel_multiplier=2, bg_upsampler=None
    )
    img_cv = cv2.imread(test_img_path)
    t = time.time()
    _, _, restored = restorer.enhance(
        img_cv, has_aligned=False, only_center_face=False, paste_back=True
    )
    elapsed = time.time() - t
    out_path = os.path.join(OUTPUTS_DIR, "test_face_enhanced.png")
    cv2.imwrite(out_path, restored)
    print(f"  PASS  Face enhanced in {elapsed:.1f}s")
    print(f"  Saved: {out_path}")
    results.append(("Face Enhancement", True, f"{elapsed:.1f}s"))
except Exception as e:
    print(f"  FAIL  {e}")
    results.append(("Face Enhancement", False, str(e)[:60]))

print("\n[TEST 3] Image Upscaling (Real-ESRGAN)...")
try:
    import cv2
    import torch
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer

    model_path = os.path.join(MODELS_DIR, "RealESRGAN_x4plus.pth")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path} - run step3 first")
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    upsampler = RealESRGANer(
        scale=4,
        model_path=model_path,
        model=model,
        tile=256,
        tile_pad=10,
        pre_pad=0,
        half=torch.cuda.is_available(),
    )
    img_cv = cv2.imread(test_img_path)
    small = cv2.resize(img_cv, (100, 100))
    t = time.time()
    output, _ = upsampler.enhance(small, outscale=4)
    elapsed = time.time() - t
    out_path = os.path.join(OUTPUTS_DIR, "test_upscaled.png")
    cv2.imwrite(out_path, output)
    print(f"  PASS  Upscaled 100x100 -> 400x400 in {elapsed:.1f}s")
    print(f"  Saved: {out_path}")
    results.append(("Upscaling", True, f"{elapsed:.1f}s"))
except Exception as e:
    print(f"  FAIL  {e}")
    results.append(("Upscaling", False, str(e)[:60]))

print("\n[TEST 4] Watermark Removal (LaMa)...")
try:
    from simple_lama_inpainting import SimpleLama

    img = Image.open(test_img_path).convert("RGB")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle([50, 50, 200, 90], fill=255)
    t = time.time()
    lama = SimpleLama()
    result = lama(img, mask)
    elapsed = time.time() - t
    out_path = os.path.join(OUTPUTS_DIR, "test_watermark_removed.png")
    result.save(out_path)
    print(f"  PASS  Watermark removed in {elapsed:.1f}s")
    print(f"  Saved: {out_path}")
    results.append(("Watermark Removal", True, f"{elapsed:.1f}s"))
except Exception as e:
    print(f"  FAIL  {e}")
    results.append(("Watermark Removal", False, str(e)[:60]))

print("\n" + "=" * 55)
print(" TEST RESULTS SUMMARY")
print("=" * 55)
passed = 0
for name, ok, info in results:
    status = "PASS" if ok else "FAIL"
    print(f"  {status}  {name:<25} {info}")
    if ok:
        passed += 1
print(f"\n  {passed}/{len(results)} models working")
if passed == len(results):
    print("\n  All models ready! Run: python step5_app.py")
else:
    print("\n  Fix the failures above, then re-run this test")
print("=" * 55)
