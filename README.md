# ShipCheckAI Proxy (FastAPI on Railway)

## Local structure
- `main.py` — FastAPI app with `/api/analyze`, `/api/analyze/batch`, `/api/health`
- `requirements.txt` — deps
- `Railway.toml` — start command & healthcheck

## Deploy (GitHub → Railway)
1. Push to your GitHub repo.
2. Railway → New Project → Deploy from GitHub → select repo.
3. In Variables set:
   - `OPENAI_API_KEY` = your key
   - `OPENAI_VISION_MODEL` = gpt-4o-mini
   - `ALLOWED_ORIGINS` = https://your-wordpress-domain (comma-separated if many)
4. Open your public domain and hit `/api/health`.

## cURL test
```bash
curl -X POST "https://YOUR-RAILWAY-DOMAIN/api/analyze"   -H "Accept: application/json"   -F "file=@/path/to/photo.jpg"
```
