# API Reference

## Base URL
```
http://127.0.0.1:8000/api
```

## Endpoints

### Upload

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload` | Upload single image |
| POST | `/api/upload/batch` | Upload multiple images |
| GET | `/api/upload/file/{file_id}` | Get uploaded file |
| GET | `/api/upload/thumb/{file_id}` | Get thumbnail |
| GET | `/api/upload/backgrounds` | List backgrounds |

### Jobs

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/jobs` | Submit processing job |
| GET | `/api/jobs` | List all jobs |
| GET | `/api/jobs/{job_id}` | Get job status |
| DELETE | `/api/jobs/{job_id}` | Cancel job |
| GET | `/api/jobs/active/list` | List active jobs |

#### Submit Job Request
```json
{
  "plugin": "background_removal",
  "file_ids": ["abc12345"],
  "params": {
    "output_mode": "transparent",
    "edge_refinement": true
  }
}
```

### Presets

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/presets` | List presets |
| POST | `/api/presets` | Create preset |
| PUT | `/api/presets/{id}` | Update preset |
| DELETE | `/api/presets/{id}` | Delete preset |

### Models

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/models` | List all models |
| POST | `/api/models/{name}/download` | Download model |
| GET | `/api/models/{name}/download-progress` | Download progress |
| DELETE | `/api/models/{name}` | Delete model |
| POST | `/api/models/{name}/unload` | Unload from GPU |
| POST | `/api/models/unload-all` | Unload all |
| GET | `/api/models/vram` | VRAM status |

### Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/settings` | App settings |
| GET | `/api/settings/system` | System info |

### WebSocket

Connect to `ws://127.0.0.1:8000/ws` for real-time job progress.

Messages:
```json
{
  "type": "job_progress",
  "job": {
    "id": "abc12345",
    "status": "running",
    "progress": 45.0,
    "message": "Processing image 1/3..."
  }
}
```

## Available Plugins

| Plugin Name | Description |
|-------------|-------------|
| `background_removal` | Remove/replace backgrounds |
| `face_enhancement` | GFPGAN/CodeFormer face restoration |
| `upscaling` | Real-ESRGAN 2x/4x/8x upscaling |
| `object_removal` | LaMa inpainting with masks |
| `watermark_removal` | EasyOCR + LaMa text/watermark removal |
| `color_grading` | LUT-based color grading with presets |
| `style_transfer` | SD 1.5 img2img + LoRA |
| `cartoon_anime` | Cartoon/anime conversion |
| `headshot_generator` | Professional headshot pipeline |
| `wedding_studio` | Batch wedding album processing |

## Interactive Docs

Full interactive API docs at:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
