# Deploying Medical Consultation App to Render.com

## Prerequisites
- GitHub account
- Render.com account (free tier works)
- Your Supabase credentials
- Your OpenAI API key

---

## Step 1: Push Code to GitHub

1. Create a new GitHub repository (e.g., `medical-consultation-app`)

2. Push your code:
```bash
cd medical_app
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/medical-consultation-app.git
git push -u origin main
```

---

## Step 2: Deploy Backend (FastAPI)

1. Go to [Render Dashboard](https://dashboard.render.com/)

2. Click **"New +"** → **"Web Service"**

3. Connect your GitHub repo

4. Configure the service:
   | Setting | Value |
   |---------|-------|
   | **Name** | `medical-api` |
   | **Region** | Oregon (or closest) |
   | **Branch** | `main` |
   | **Root Directory** | `backend` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | **Plan** | Free |

5. Add **Environment Variables** (click "Advanced" → "Add Environment Variable"):
   | Key | Value |
   |-----|-------|
   | `SUPABASE_URL` | `https://your-project.supabase.co` |
   | `SUPABASE_KEY` | `your-supabase-anon-key` |
   | `OPENAI_API_KEY` | `sk-your-openai-key` |

6. Click **"Create Web Service"**

7. Wait for deployment (~2-3 minutes)

8. **Copy your backend URL** (e.g., `https://medical-api-xxxx.onrender.com`)

9. Test it: Visit `https://medical-api-xxxx.onrender.com/health`
   - Should return: `{"status": "healthy", "code": 200}`

---

## Step 3: Deploy Frontend (Streamlit)

1. Click **"New +"** → **"Web Service"** again

2. Connect the same GitHub repo

3. Configure the service:
   | Setting | Value |
   |---------|-------|
   | **Name** | `medical-frontend` |
   | **Region** | Oregon (same as backend) |
   | **Branch** | `main` |
   | **Root Directory** | `frontend` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |
   | **Plan** | Free |

4. Add **Environment Variables**:
   | Key | Value |
   |-----|-------|
   | `BACKEND_URL` | `https://medical-api-xxxx.onrender.com` (your backend URL from Step 2) |

5. Click **"Create Web Service"**

6. Wait for deployment (~2-3 minutes)

7. Your app is live at: `https://medical-frontend-xxxx.onrender.com`

---

## Alternative: Deploy via Blueprint (render.yaml)

If you prefer automatic setup:

1. Push code to GitHub (including `render.yaml` in root)

2. Go to Render Dashboard → **"New +"** → **"Blueprint"**

3. Connect your repo

4. Render will detect `render.yaml` and create both services

5. **You still need to manually set environment variables** in each service's settings

---

## Important Notes

### Free Tier Limitations
- Services spin down after 15 minutes of inactivity
- First request after sleep takes ~30-60 seconds (cold start)
- 750 free hours/month across all services

### Keep Services Awake (Optional)
To prevent cold starts, you can:
- Upgrade to paid tier ($7/month per service)
- Use a cron job to ping `/health` every 14 minutes

### Troubleshooting

**Backend won't start:**
- Check Render logs for errors
- Verify all 3 environment variables are set correctly
- Make sure Supabase URL doesn't have trailing slash

**Frontend can't connect to backend:**
- Verify `BACKEND_URL` is correct (no trailing slash)
- Check backend is running: visit `{BACKEND_URL}/health`
- Check browser console for CORS errors (shouldn't happen, CORS is enabled)

**Audio recording not working:**
- Render uses HTTPS, so microphone access should work
- Some browsers block mic on non-HTTPS (Render provides HTTPS by default)

---

## Your Deployed URLs

After deployment, you'll have:

| Service | URL |
|---------|-----|
| Backend API | `https://medical-api-xxxx.onrender.com` |
| API Docs | `https://medical-api-xxxx.onrender.com/docs` |
| Frontend App | `https://medical-frontend-xxxx.onrender.com` |

---

## Updating Your App

After making changes locally:

```bash
git add .
git commit -m "Your update message"
git push
```

Render auto-deploys on every push to `main` branch.
