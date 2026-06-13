AI PHOTO STUDIO - Phase 1
==========================

SETUP ORDER (follow exactly):
1. Double-click step2_install_packages.bat
   Wait for all 6 packages to install (10-15 min first time)

2. Run: python step3_download_models.py
   Downloads GFPGAN and Real-ESRGAN weights (~500MB total)

3. Run: python step4_test_models.py
   Tests all 4 models. All should show PASS.

4. Run: python step5_app.py
   Starts the web UI at http://localhost:7860

SERVICES INCLUDED:
- Background Removal (rembg)
- Background Replacement (solid color or custom image)
- Face Enhancement (GFPGAN v1.4)
- Image Upscaling 2x-4x (Real-ESRGAN)
- Watermark Removal (LaMa)
- Full Portrait Pipeline (all 3 steps in one click)

ALL OUTPUTS saved automatically to: outputs/ folder

PRICING GUIDE (Fiverr / local):
- Background removal: Rs 50-150 per image
- Face enhancement: Rs 100-300 per photo
- Upscaling old photo: Rs 150-400 per photo
- Watermark removal: Rs 50-200 per image
- Full portrait package: Rs 300-800 per photo

FOLDER STRUCTURE:
ai_photo_studio/
  models/        <- downloaded model weights live here
  inputs/        <- put client photos here
  outputs/       <- all processed results saved here
  backgrounds/   <- add your own background images here
  temp/          <- temporary working files
