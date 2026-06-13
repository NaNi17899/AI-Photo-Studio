import os
import time
import numpy as np
from PIL import Image
import gradio as gr

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
BACKGROUNDS_DIR = os.path.join(BASE_DIR, "backgrounds")
for d in [OUTPUTS_DIR, BACKGROUNDS_DIR]:
    os.makedirs(d, exist_ok=True)

print("Loading models... please wait")

print("  Loading rembg...")
from rembg import remove as rembg_remove

print("  Loading GFPGAN...")
from gfpgan import GFPGANer
import cv2

gfpgan_model = GFPGANer(
    model_path=os.path.join(MODELS_DIR, "GFPGANv1.4.pth"),
    upscale=2,
    arch="clean",
    channel_multiplier=2,
    bg_upsampler=None,
)

print("  Loading Real-ESRGAN...")
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

_esrgan_model = RRDBNet(
    num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4
)
esrgan = RealESRGANer(
    scale=4,
    model_path=os.path.join(MODELS_DIR, "RealESRGAN_x4plus.pth"),
    model=_esrgan_model,
    tile=256,
    tile_pad=10,
    pre_pad=0,
    half=torch.cuda.is_available(),
)

print("  Loading LaMa...")
from simple_lama_inpainting import SimpleLama

lama_model = SimpleLama()

print("All models loaded!\n")

SAMPLE_BACKGROUNDS = {
    "White studio": (255, 255, 255),
    "Black studio": (20, 20, 20),
    "Sky blue": (135, 206, 235),
    "Soft grey": (240, 240, 240),
    "Forest green": (34, 85, 34),
    "Warm cream": (255, 248, 220),
}


def save_output(img: Image.Image, prefix: str) -> str:
    fname = f"{prefix}_{int(time.time())}.png"
    path = os.path.join(OUTPUTS_DIR, fname)
    img.save(path)
    return path


def remove_background(image):
    if image is None:
        return None, "Please upload an image"
    try:
        inp = Image.fromarray(image).convert("RGBA")
        out = rembg_remove(inp)
        save_output(out, "bg_removed")
        return np.array(out), "Background removed successfully"
    except Exception as e:
        return None, f"Error: {e}"


def remove_and_replace(image, bg_choice, custom_bg):
    if image is None:
        return None, "Please upload an image"
    try:
        inp = Image.fromarray(image).convert("RGBA")
        removed = rembg_remove(inp)
        if custom_bg is not None:
            bg = Image.fromarray(custom_bg).convert("RGBA").resize(removed.size)
        else:
            color = SAMPLE_BACKGROUNDS.get(bg_choice, (255, 255, 255))
            bg = Image.new("RGBA", removed.size, color + (255,))
        bg.paste(removed, mask=removed.split()[3])
        result = bg.convert("RGB")
        save_output(result, "bg_replaced")
        return np.array(
            result
        ), f"Background replaced with: {bg_choice if custom_bg is None else 'custom image'}"
    except Exception as e:
        return None, f"Error: {e}"


def enhance_face(image):
    if image is None:
        return None, "Please upload an image"
    try:
        img_cv = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        _, _, restored = gfpgan_model.enhance(
            img_cv, has_aligned=False, only_center_face=False, paste_back=True
        )
        result = cv2.cvtColor(restored, cv2.COLOR_BGR2RGB)
        save_output(Image.fromarray(result), "face_enhanced")
        return result, "Face enhanced successfully"
    except Exception as e:
        return None, f"Error: {e}"


def upscale_image(image, scale):
    if image is None:
        return None, "Please upload an image"
    try:
        img_cv = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        output, _ = esrgan.enhance(img_cv, outscale=scale)
        result = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        h, w = image.shape[:2]
        nh, nw = result.shape[:2]
        save_output(Image.fromarray(result), "upscaled")
        return result, f"Upscaled from {w}x{h} to {nw}x{nh}"
    except Exception as e:
        return None, f"Error: {e}"


def remove_watermark(image, mask_image):
    if image is None:
        return None, "Please upload an image"
    if mask_image is None:
        return None, "Please draw the mask over the watermark area"
    try:
        img_pil = Image.fromarray(image).convert("RGB")
        mask_pil = Image.fromarray(mask_image).convert("L")
        if img_pil.size != mask_pil.size:
            mask_pil = mask_pil.resize(img_pil.size)
        result = lama_model(img_pil, mask_pil)
        save_output(result, "watermark_removed")
        return np.array(result), "Watermark removed successfully"
    except Exception as e:
        return None, f"Error: {e}"


def full_pipeline(image):
    if image is None:
        return None, None, None, "Please upload an image"
    try:
        img_cv = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        _, _, restored = gfpgan_model.enhance(
            img_cv, has_aligned=False, only_center_face=False, paste_back=True
        )
        enhanced_cv = restored

        inp = Image.fromarray(cv2.cvtColor(enhanced_cv, cv2.COLOR_BGR2RGB))
        bg_removed = rembg_remove(inp.convert("RGBA"))

        bg = Image.new("RGBA", bg_removed.size, (255, 255, 255, 255))
        bg.paste(bg_removed, mask=bg_removed.split()[3])
        final = bg.convert("RGB")

        small = cv2.resize(enhanced_cv, (200, 200))
        upscaled_small, _ = esrgan.enhance(small, outscale=2)

        save_output(final, "full_pipeline")
        return (
            cv2.cvtColor(restored, cv2.COLOR_BGR2RGB),
            np.array(bg_removed),
            np.array(final),
            "Full pipeline complete: Enhanced -> Background removed -> White background applied",
        )
    except Exception as e:
        return None, None, None, f"Error: {e}"


CSS = """
.gradio-container { max-width: 1000px !important; margin: auto !important; }
.status-box { font-size: 13px; padding: 8px 12px; border-radius: 8px; }
"""

with gr.Blocks(css=CSS, title="AI Photo Studio") as app:
    gr.Markdown("""
# AI Photo Studio
### Professional photo editing powered by AI — Background Removal · Face Enhancement · Upscaling · Watermark Removal
""")

    with gr.Tabs():
        with gr.TabItem("Background Removal"):
            gr.Markdown(
                "Remove background from any photo. Works best on portraits and product photos."
            )
            with gr.Row():
                with gr.Column():
                    bg_input = gr.Image(label="Upload photo", type="numpy")
                    bg_btn = gr.Button("Remove Background", variant="primary")
                with gr.Column():
                    bg_output = gr.Image(label="Result (transparent background)")
                    bg_status = gr.Textbox(label="Status", interactive=False)
            bg_btn.click(remove_background, inputs=bg_input, outputs=[bg_output, bg_status])

        with gr.TabItem("Background Replacement"):
            gr.Markdown("Remove background and replace with a solid color or your own image.")
            with gr.Row():
                with gr.Column():
                    bgr_input = gr.Image(label="Upload photo", type="numpy")
                    bgr_choice = gr.Dropdown(
                        choices=list(SAMPLE_BACKGROUNDS.keys()),
                        value="White studio",
                        label="Background color",
                    )
                    bgr_custom = gr.Image(
                        label="Or upload custom background (optional)", type="numpy"
                    )
                    bgr_btn = gr.Button("Replace Background", variant="primary")
                with gr.Column():
                    bgr_output = gr.Image(label="Result")
                    bgr_status = gr.Textbox(label="Status", interactive=False)
            bgr_btn.click(
                remove_and_replace,
                inputs=[bgr_input, bgr_choice, bgr_custom],
                outputs=[bgr_output, bgr_status],
            )

        with gr.TabItem("Face Enhancement"):
            gr.Markdown(
                "Enhance face quality — sharpen eyes, smooth skin, fix blur. Best for portraits and wedding photos."
            )
            with gr.Row():
                with gr.Column():
                    face_input = gr.Image(label="Upload portrait", type="numpy")
                    face_btn = gr.Button("Enhance Face", variant="primary")
                with gr.Column():
                    face_output = gr.Image(label="Enhanced result")
                    face_status = gr.Textbox(label="Status", interactive=False)
            face_btn.click(enhance_face, inputs=face_input, outputs=[face_output, face_status])

        with gr.TabItem("Image Upscaling"):
            gr.Markdown(
                "Upscale low-resolution images up to 4×. Perfect for old family photos and blurry product shots."
            )
            with gr.Row():
                with gr.Column():
                    up_input = gr.Image(label="Upload image", type="numpy")
                    up_scale = gr.Slider(
                        minimum=2, maximum=4, step=1, value=4, label="Upscale factor"
                    )
                    up_btn = gr.Button("Upscale Image", variant="primary")
                with gr.Column():
                    up_output = gr.Image(label="Upscaled result")
                    up_status = gr.Textbox(label="Status", interactive=False)
            up_btn.click(upscale_image, inputs=[up_input, up_scale], outputs=[up_output, up_status])

        with gr.TabItem("Watermark Removal"):
            gr.Markdown(
                "Remove watermarks, text overlays, or unwanted objects. Draw a white mask over the area to remove."
            )
            with gr.Row():
                with gr.Column():
                    wm_input = gr.Image(label="Upload image", type="numpy")
                    wm_mask = gr.Image(
                        label="Upload mask (white = area to remove, black = keep)", type="numpy"
                    )
                    wm_btn = gr.Button("Remove Watermark", variant="primary")
                with gr.Column():
                    wm_output = gr.Image(label="Clean result")
                    wm_status = gr.Textbox(label="Status", interactive=False)
            wm_btn.click(
                remove_watermark, inputs=[wm_input, wm_mask], outputs=[wm_output, wm_status]
            )

        with gr.TabItem("Full Pipeline (Portrait)"):
            gr.Markdown(
                "Complete portrait processing in one click: Face Enhancement → Background Removal → White Studio Background."
            )
            with gr.Row():
                with gr.Column():
                    fp_input = gr.Image(label="Upload portrait", type="numpy")
                    fp_btn = gr.Button("Run Full Pipeline", variant="primary")
                with gr.Column():
                    fp_enhanced = gr.Image(label="Step 1: Face enhanced")
                    fp_nobg = gr.Image(label="Step 2: Background removed")
                    fp_final = gr.Image(label="Step 3: Final result")
                    fp_status = gr.Textbox(label="Status", interactive=False)
            fp_btn.click(
                full_pipeline, inputs=fp_input, outputs=[fp_enhanced, fp_nobg, fp_final, fp_status]
            )

    gr.Markdown("""
---
**Outputs saved to:** `outputs/` folder in project directory
""")

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print(" Starting AI Photo Studio")
    print(" Open your browser at: http://localhost:7860")
    print("=" * 50 + "\n")
    app.launch(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True)
