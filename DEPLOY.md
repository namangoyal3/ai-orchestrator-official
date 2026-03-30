# Deployment Guide — Railway (Backend) + Vercel (Frontend)

## Prerequisites
- Railway account: https://railway.app
- Vercel account: https://vercel.com
- Railway CLI: `npm install -g @railway/cli`
- Vercel CLI: `npm install -g vercel`

---

## Part 1 — Deploy Backend to Railway

### Step 1: Login and create a project
```bash
railway login
railway init
```
Select "Empty Project" and name it `ai-gateway-backend`.

### Step 2: Link your repo or deploy from local
```bash
cd backend
railway up
```
Railway auto-detects the `Dockerfile` and builds it.

### Step 3: Set environment variables in Railway dashboard
Go to your service → Variables → Add Raw:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
SECRET_KEY=<run: openssl rand -hex 32>
DEBUG=false
```
Optional (for multi-provider routing):
```
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_API_KEY=your-google-api-key
```

### Step 4: Add a persistent volume for SQLite
In Railway dashboard → your service → Volumes → Add Volume:
- Mount path: `/data`
- This ensures the database persists across deploys.

### Step 5: Verify deployment
```
https://<your-service>.railway.app/health
```
Should return: `{"status": "ok", ...}`

### Step 6: Note your backend URL
```
https://<your-service>.railway.app
```
You will need this for the frontend deploy.

---

## Part 2 — Deploy Frontend to Vercel

### Step 1: Set environment variables
Create `frontend/.env.production`:
```
NEXT_PUBLIC_API_URL=https://<your-backend>.railway.app
BACKEND_URL=https://<your-backend>.railway.app
```

### Step 2: Deploy via Vercel CLI
```bash
cd frontend
vercel --prod
```
When prompted:
- Link to existing project or create new
- Framework: Next.js (auto-detected)
- Build command: `npm run build` (default)
- Output: `.next` (default)

### Step 3: Set env vars in Vercel dashboard
Go to Project → Settings → Environment Variables:
```
NEXT_PUBLIC_API_URL = https://<your-backend>.railway.app
BACKEND_URL = https://<your-backend>.railway.app
```
Redeploy after setting variables.

### Step 4: Verify
Open your Vercel URL — the dashboard should load and connect to Railway.

---

## Part 3 — Local Development

```bash
# Copy env file
cp backend/.env.example backend/.env
# Edit with your API keys
nano backend/.env

# Start everything
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

---

## Demo API Key
The seed script auto-creates a demo key on first run:
```
gw-demo-key-change-in-production-12345678
```
Use it as `X-API-Key` header for testing. Replace before going to production.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 500 on `/v1/query` | Check `ANTHROPIC_API_KEY` is set in Railway vars |
| Database errors | Ensure `/data` volume is mounted in Railway |
| CORS errors | Verify `NEXT_PUBLIC_API_URL` matches your Railway URL exactly |
| Frontend can't reach backend | Check `BACKEND_URL` env var in Vercel settings |
| Cold start slow | Railway hobby plan — first request after sleep takes ~3s |
