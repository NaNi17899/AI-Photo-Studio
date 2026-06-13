# Project File Structure

```text
ai_photo_studio_phase1/
└── ai_photo_studio/
    ├── backend/
    │   ├── api/
    │   │   ├── __init__.py
    │   │   ├── jobs.py
    │   │   ├── models_api.py
    │   │   ├── presets.py
    │   │   ├── settings_api.py
    │   │   ├── upload.py
    │   │   └── ws.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── gpu_utils.py
    │   │   ├── image_utils.py
    │   │   ├── job_queue.py
    │   │   ├── model_manager.py
    │   │   ├── plugin_base.py
    │   │   └── plugin_registry.py
    │   ├── models/
    │   │   └── __init__.py
    │   ├── plugins/
    │   │   ├── background_removal/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── cartoon_anime/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── color_grading/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── face_enhancement/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── headshot_generator/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── object_removal/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── style_transfer/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── upscaling/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── watermark_removal/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   ├── wedding_studio/
    │   │   │   ├── __init__.py
    │   │   │   └── plugin.py
    │   │   └── __init__.py
    │   ├── storage/
    │   │   ├── __init__.py
    │   │   └── file_manager.py
    │   ├── __init__.py
    │   ├── config.py
    │   ├── database.py
    │   └── main.py
    ├── backgrounds/
    ├── data/
    │   ├── backgrounds/
    │   ├── db/
    │   │   └── photo_studio.db
    │   ├── luts/
    │   ├── models/
    │   │   ├── loras/
    │   │   ├── GFPGANv1.4.pth
    │   │   ├── RealESRGAN_x2plus.pth
    │   │   ├── RealESRGAN_x4plus.pth
    │   │   ├── RealESRGAN_x4plus_anime_6B.pth
    │   │   ├── codeformer.pth
    │   │   ├── detection_Resnet50_Final.pth
    │   │   └── parsing_parsenet.pth
    │   ├── outputs/
    │   │   └── 11dbbd2c_cartoon_anime_cartoon_1781322851.png
    │   ├── uploads/
    │   │   ├── thumbs/
    │   │   │   ├── 11dbbd2c_thumb.webp
    │   │   │   └── 5bce045a_thumb.webp
    │   │   ├── 11dbbd2c.png
    │   │   └── 5bce045a.jpg
    │   └── photo_studio.log
    ├── docker/
    │   ├── Dockerfile
    │   └── docker-compose.yml
    ├── docs/
    │   ├── API.md
    │   ├── CLOUDFLARE_TUNNEL.md
    │   ├── DEPLOYMENT.md
    │   └── SETUP.md
    ├── frontend/
    │   ├── public/
    │   │   └── favicon.svg
    │   ├── src/
    │   │   ├── api/
    │   │   │   └── client.js
    │   │   ├── components/
    │   │   │   ├── BeforeAfterSlider.jsx
    │   │   │   ├── Header.jsx
    │   │   │   ├── ImageUploader.jsx
    │   │   │   ├── ProgressBar.jsx
    │   │   │   └── Sidebar.jsx
    │   │   ├── hooks/
    │   │   │   └── useWebSocket.js
    │   │   ├── pages/
    │   │   │   ├── BatchProcessing.jsx
    │   │   │   ├── Dashboard.jsx
    │   │   │   ├── FeaturePage.jsx
    │   │   │   ├── ModelManager.jsx
    │   │   │   └── Settings.jsx
    │   │   ├── App.jsx
    │   │   ├── index.css
    │   │   └── main.jsx
    │   ├── index.html
    │   ├── package-lock.json
    │   ├── package.json
    │   └── vite.config.js
    ├── gfpgan/
    │   └── weights/
    │       ├── detection_Resnet50_Final.pth
    │       └── parsing_parsenet.pth
    ├── models/
    │   ├── GFPGANv1.4.pth
    │   └── RealESRGAN_x4plus.pth
    ├── outputs/
    │   ├── bg_removed_1781244281.png
    │   ├── bg_removed_1781244312.png
    │   ├── bg_removed_1781244354.png
    │   ├── bg_removed_1781244376.png
    │   ├── bg_replaced_1781244417.png
    │   ├── bg_replaced_1781244427.png
    │   ├── bg_replaced_1781244434.png
    │   ├── face_enhanced_1781244454.png
    │   ├── test_bg_removed.png
    │   ├── test_face_enhanced.png
    │   ├── test_upscaled.png
    │   ├── test_watermark_removed.png
    │   └── upscaled_1781244470.png
    ├── scripts/
    │   ├── download_models.py
    │   ├── install.bat
    │   └── start.bat
    ├── temp/
    │   └── test_input.png
    ├── tests/
    │   └── test_all.py
    ├── {models,inputs,outputs,backgrounds,temp}/
    ├── .env.example
    ├── README.md
    ├── README.txt
    ├── pyproject.toml
    ├── pyrightconfig.json
    ├── requirements.txt
    ├── step1_verify_setup.py
    ├── step2_install_packages.bat
    ├── step3_download_models.py
    ├── step4_test_models.py
    └── step5_app.py
```
