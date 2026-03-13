# Deploying PropertyLens to Render

This guide covers setup before deployment, deployment order, and where secrets are stored.

---

## 1. Setup Before Deployment

### A. External services (set up first)

| Service | Where | What to get |
|---------|-------|-------------|
| **Qdrant Cloud** | [cloud.qdrant.io](https://cloud.qdrant.io) | Create a cluster → `QDRANT_URL`, `QDRANT_API_KEY` |
| **Redis** | Render add-on or [Upstash](https://upstash.com) | `REDIS_URL` |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | `OPENAI_API_KEY` |
| **Tavily** | [tavily.com](https://tavily.com) | `TAVILY_API_KEY` |
| **Cohere** (optional) | [cohere.com](https://cohere.com) | `COHERE_API_KEY` for reranking |

### B. Reference PDFs

- Reference PDFs in `backend/data/` are auto-ingested on backend startup
- Ensure `backend/data/` is committed to the repo so Render can access it
- If the folder is empty or missing, ingestion will skip; you can add PDFs later and redeploy

### C. Repo structure

- Ensure `ai-realtor/backend` and `ai-realtor/frontend` exist in your repo
- If `ai-realtor` is the repo root, update `rootDir` in `render.yaml` to `backend` and `frontend` (remove `ai-realtor/` prefix)

---

## 2. Deployment Order: Backend First, Then Frontend

**Yes, you can deploy one service at a time.**

### Step 1: Deploy backend

1. Create a **Web Service** for the backend
2. Connect your GitHub repo
3. **Root Directory:** `ai-realtor/backend` (or `backend` if ai-realtor is repo root)
4. **Build:** `uv sync` (or `pip install .` if uv is not available on Render)
5. **Start:** `uv run uvicorn main:app --host 0.0.0.0 --port $PORT` (or `uvicorn main:app --host 0.0.0.0 --port $PORT` if using pip)
6. Add all env vars (see Section 4 below). For `CORS_ORIGINS`, use a placeholder for now (e.g. `http://localhost:3000`) or leave default
7. Deploy
8. **Verify:**
   - Visit `https://your-backend.onrender.com/health` → should return `{"status":"ok"}`
   - Backend must be reachable before frontend can use it

### Step 2: Deploy frontend

1. Create a **Web Service** for the frontend
2. Connect the same repo
3. **Root Directory:** `ai-realtor/frontend` (or `frontend` if ai-realtor is repo root)
4. **Build:** `npm install && npm run build`
5. **Start:** `npm start`
6. Add env vars: `NEXT_PUBLIC_BACKEND_URL` and `BACKEND_URL` = `https://your-backend.onrender.com`
7. Deploy
8. Update backend `CORS_ORIGINS` to include your frontend URL: `https://your-frontend.onrender.com`
9. Redeploy backend if needed

### Step 3: Connect them

- Set frontend env `NEXT_PUBLIC_BACKEND_URL` and `BACKEND_URL` to the backend URL
- Set backend env `CORS_ORIGINS` to include the frontend URL (comma-separated if multiple)

---

## 3. Secrets in Render Dashboard

**Yes. All secrets and env vars are stored in the Render Dashboard.**

- **Dashboard → Your Service → Environment**
- Add each variable there; Render does not read from `.env` or `.env.local` in your repo
- Mark sensitive values as **Secret** (they will be encrypted and hidden)
- Never commit `.env` or `.env.local` to git

---

## 4. Environment Variables by Service

### Backend

| Variable | Required | Secret | Example / Notes |
|----------|----------|--------|-----------------|
| `OPENAI_API_KEY` | Yes | Yes | `sk-...` |
| `QDRANT_URL` | Yes | Yes | `https://xxx.gcp.cloud.qdrant.io` |
| `QDRANT_API_KEY` | Yes | Yes | From Qdrant Cloud |
| `REDIS_URL` | Yes | Yes | `redis://...` or from Render Redis add-on |
| `TAVILY_API_KEY` | Yes | Yes | `tvly-...` |
| `CORS_ORIGINS` | Yes | No | `https://your-frontend.onrender.com` |
| `COHERE_API_KEY` | No | Yes | Optional; for reranking |
| `LLM_MODEL` | No | No | Default `gpt-4o-mini` |

### Frontend

| Variable | Required | Secret | Example / Notes |
|----------|----------|--------|-----------------|
| `NEXT_PUBLIC_BACKEND_URL` | Yes | No | `https://your-backend.onrender.com` |
| `BACKEND_URL` | Yes | No | Same as above (for API routes) |

---

## 5. Using the Blueprint (render.yaml)

1. Push `render.yaml` to your repo (at repo root or in `ai-realtor/`)
2. In Render: **Dashboard → New → Blueprint**
3. Connect the repo; Render will detect the blueprint
4. Configure env vars when prompted (they are not in the blueprint for security)
5. Create the Redis add-on if using the `databases` section, or add `REDIS_URL` manually

---

## 6. Free Tier Notes

- Services spin down after 15 minutes of inactivity
- First request after spin-down: ~30–60 second cold start
- 750 free instance hours per month (shared across services)
- For more stable uptime, use paid plans (~$7/month per service)

---

## 7. Summary

| Question | Answer |
|----------|--------|
| Setup before deploy? | Qdrant Cloud, Redis, API keys (OpenAI, Tavily). Reference PDFs in `backend/data/`. |
| Deploy order? | Backend first → verify `/health` → then frontend → update `CORS_ORIGINS`. |
| Where are secrets? | Render Dashboard → Service → Environment (never in repo). |
