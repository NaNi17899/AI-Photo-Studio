# Deployment Guide

## Local Deployment (Windows)

### Prerequisites
- Python 3.10+
- Node.js 18+
- NVIDIA GPU with CUDA drivers
- 16GB RAM

### Steps
1. Run `scripts\install.bat`
2. Run `python scripts\download_models.py`
3. Run `scripts\start.bat`
4. Open http://127.0.0.1:8000

## Docker Deployment

### Prerequisites
- Docker with [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

### Steps
```bash
cd docker
docker-compose up --build -d
```

### GPU Passthrough Verification
```bash
docker exec ai-photo-studio python -c "import torch; print(torch.cuda.is_available())"
```

## Production Deployment (VPS/Cloud)

### 1. Use a GPU Cloud Provider
- RunPod
- Vast.ai
- Lambda Labs
- AWS g4dn instances

### 2. Clone and Install
```bash
git clone <your-repo>
cd ai_photo_studio
chmod +x scripts/install.sh
./scripts/install.sh
```

### 3. Run with Systemd
Create `/etc/systemd/system/ai-photo-studio.service`:
```ini
[Unit]
Description=AI Photo Studio
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ai_photo_studio
ExecStart=/home/ubuntu/ai_photo_studio/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ai-photo-studio
sudo systemctl start ai-photo-studio
```

### 4. Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name studio.yourdomain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5. SSL with Certbot
```bash
sudo certbot --nginx -d studio.yourdomain.com
```

## SaaS Deployment Path

For future SaaS deployment:
1. Replace SQLite with PostgreSQL
2. Add JWT authentication
3. Add Stripe billing integration
4. Use Redis for job queue (replace in-memory queue)
5. Use S3/R2 for file storage
6. Add rate limiting
7. Containerize with Kubernetes
