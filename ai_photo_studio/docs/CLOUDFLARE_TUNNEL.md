# Cloudflare Tunnel Setup

Expose your local AI Photo Studio to the internet securely using Cloudflare Tunnel.

## Prerequisites

1. A Cloudflare account (free tier works)
2. A domain managed by Cloudflare (or use the free `.trycloudflare.com` subdomain)
3. `cloudflared` CLI installed

## Install cloudflared

### Windows
```bash
winget install --id Cloudflare.cloudflared
# Or download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```

## Quick Tunnel (No domain required)

For testing, use a free temporary tunnel:

```bash
cloudflared tunnel --url http://localhost:8000
```

This gives you a random `*.trycloudflare.com` URL — perfect for sharing temporarily.

## Named Tunnel (Production)

### 1. Authenticate
```bash
cloudflared tunnel login
```

### 2. Create Tunnel
```bash
cloudflared tunnel create ai-photo-studio
```

### 3. Configure DNS
```bash
cloudflared tunnel route dns ai-photo-studio studio.yourdomain.com
```

### 4. Create Config
Create `~/.cloudflared/config.yml`:
```yaml
tunnel: ai-photo-studio
credentials-file: /home/user/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: studio.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

### 5. Run
```bash
cloudflared tunnel run ai-photo-studio
```

### 6. Run as Windows Service (auto-start)
```bash
cloudflared service install
```

## Security Notes

- The tunnel encrypts all traffic — no need for SSL certificates
- Consider adding Cloudflare Access policies to restrict who can access your studio
- The application doesn't have built-in authentication — use Cloudflare Access for auth
