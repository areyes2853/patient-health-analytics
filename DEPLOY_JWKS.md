# 🚀 Quick JWKS Deployment to Dockploy

Deploy just the JWKS endpoint so Epic can verify your public key immediately!

## Why This Works

Epic needs to fetch your JWKS file from:
```
https://health-analytics.duckdev.me/api/backend/.well-known/jwks.json
```

By deploying this minimal server, Epic can:
1. ✅ Validate your JWK Set URL
2. ✅ Complete your app registration
3. ✅ Let you test locally immediately

## 🎯 Deployment Options

### Option A: Deploy via Dockploy Dashboard (Easiest)

1. **Create New App in Dockploy**
   ```
   App Name: jwks-server
   Type: Docker
   Domain: health-analytics.duckdev.me
   ```

2. **Connect to Your Git Repo**
   - Push the minimal files to a branch
   - Or use Dockploy's file upload

3. **Configure Build**
   ```
   Dockerfile: Dockerfile.jwks
   Port: 5000
   ```

4. **Deploy!**

### Option B: Deploy via SSH/SCP (Quickest)

If you have SSH access to your Dockploy server:

```bash
# 1. SSH into your server
ssh user@your-dockploy-server

# 2. Create app directory
mkdir -p /opt/jwks-server
cd /opt/jwks-server

# 3. Create jwks_server.py (copy content from the file)
nano jwks_server.py
# Paste the content and save

# 4. Create requirements
echo "flask==2.3.2" > requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt

# 5. Install and run
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 jwks_server:app --daemon

# 6. Configure Nginx/Caddy to reverse proxy to port 5000
```

### Option C: Docker Compose on Dockploy

```yaml
version: '3.8'

services:
  jwks:
    build:
      context: .
      dockerfile: Dockerfile.jwks
    ports:
      - "5000:5000"
    restart: unless-stopped
```

## 📦 Files to Deploy

You only need these 3 files:
```
jwks_server.py          ← The minimal Flask app
requirements-jwks.txt   ← Just Flask + Gunicorn
Dockerfile.jwks         ← Docker build config
```

## ✅ Verify It Works

After deployment, test:

```bash
# Should return your JWKS
curl https://health-analytics.duckdev.me/api/backend/.well-known/jwks.json

# Should see:
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "epic-backend-key",
      ...
    }
  ]
}
```

## 🔄 Then Go Back to Epic

1. **In Epic's app settings**, enter:
   ```
   JWK Set URL: https://health-analytics.duckdev.me/api/backend/.well-known/jwks.json
   ```

2. **Epic will validate** - this time it should work! ✅

3. **Get your Client ID** (or it should already be: `d796e70b-08b2-48d7-8168-b410d6c35f19`)

4. **Test locally immediately:**
   ```bash
   python test_backend_auth.py
   ```

## 🎨 Alternative: Static File Hosting

If Dockploy supports static file hosting, you could just upload `jwks.json`:

```bash
# Upload to:
/var/www/health-analytics/api/backend/.well-known/jwks.json
```

Then configure Nginx/Caddy to serve it at that path.

## 🚀 Quick Git Push Method

If Dockploy is connected to your GitHub:

```bash
# 1. Create a separate branch for JWKS deployment
git checkout -b jwks-only

# 2. Remove everything except JWKS files
git rm -r --cached .
git add jwks_server.py requirements-jwks.txt Dockerfile.jwks

# 3. Commit and push
git commit -m "Minimal JWKS server for Epic verification"
git push origin jwks-only

# 4. In Dockploy, deploy from 'jwks-only' branch
```

## 🎯 Expected Flow

```
1. Deploy JWKS server → health-analytics.duckdev.me
2. Test URL works → curl returns JWKS
3. Update Epic app → Validate JWK Set URL ✅
4. Test locally → python test_backend_auth.py ✅
5. Later: Deploy full app → Replace JWKS server
```

## 📝 Notes

- **This is temporary** - Once you deploy your full app, it will serve JWKS itself
- **No secrets needed** - JWKS only contains your PUBLIC key
- **Very lightweight** - Runs in <50MB container
- **Can coexist** - Full app can replace this later

---

## 🆘 Troubleshooting

### JWKS URL returns 404
- Check domain configuration in Dockploy
- Verify app is running: `docker ps`
- Check logs: `docker logs jwks-server`

### Epic still says "Not Found"
- Wait 1-2 minutes for DNS/deployment
- Test with curl first
- Check HTTPS is working (not HTTP)

### Port conflicts
- Change port in Dockploy if 5000 is taken
- Update Dockerfile.jwks accordingly

---

**Ready to deploy?** Which method works best for your Dockploy setup?
