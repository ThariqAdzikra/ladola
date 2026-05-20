# ChilliGuard

AI-powered chili disease detection with a CNN backend and a Next.js frontend.

## Structure

```text
ChilliGuard/
|-- backend/    # FastAPI API + PyTorch inference
|   |-- model/  # Trained model artifacts (.pth and .json)
`-- frontend/   # Next.js app
```

## Dataset

The training dataset has been removed from the production repository to reduce size. The model is already trained and stored in `backend/model/`.

The model detects 9 classes:

1. Antraknosa (`chilli_anthracnos`)
2. Layu Fusarium (`chilli_damping_off`)
3. Sehat (Buah) (`chilli_healthy_fruit`)
4. Sehat (Daun) (`chilli_healthy_leaf`)
5. Virus Keriting Daun (`chilli_leaf_curl_virus`)
6. Bercak Daun (`chilli_leaf_spot`)
7. Virus Mottle Vena (`chilli_veinal_mottle_virus`)
8. Kutu Kebul (`chilli_whitefly`)
9. Menguning (`chilli_yellowish`)

## Local Setup

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the API:

```powershell
uvicorn main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

## Cloud Run Deployment

Production deployment uses a single root `Dockerfile`. The container packages both frontend and backend, served via Nginx on port `8080`.

### Deployment Steps

1.  **Build and Push Image:**
    ```bash
    gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/chilliguard
    ```

2.  **Deploy to Cloud Run:**
    ```bash
    gcloud run deploy chilliguard \
      --image gcr.io/YOUR_PROJECT_ID/chilliguard \
      --platform managed \
      --port 8080 \
      --allow-unauthenticated
    ```

### Required Environment Variables

Set these in the Cloud Run service configuration (**Variables & secrets → Environment variables**).

You can copy-paste the block below and replace the values that are marked with `<>`:

```env
# App/runtime
APP_ENV=production

# CORS for backend (comma-separated allowed origins)
ALLOWED_ORIGINS=https://chilliguard.dpdns.org

# Database
DATABASE_URL=<your_postgres_url>

# Gemini / Generative AI (backend reads GEMINI_API_KEY or GOOGLE_API_KEY)
GEMINI_API_KEY=<your_gemini_api_key>
# (optional alternative name)
# GOOGLE_API_KEY=<your_gemini_api_key>
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_FALLBACK_MODELS=gemini-2.5-flash

# NextAuth (frontend)
NEXTAUTH_URL=https://chilliguard.dpdns.org
NEXTAUTH_SECRET=<your_random_long_secret>
GOOGLE_CLIENT_ID=<your_google_oauth_client_id>
GOOGLE_CLIENT_SECRET=<your_google_oauth_client_secret>

# Frontend → backend (server-side calls from Next.js route handlers)
# In this single-container deployment, the backend is available on localhost:8000.
BACKEND_API_URL=http://127.0.0.1:8000

# Browser → API base URL used by the UI (points to the public Cloud Run URL)
NEXT_PUBLIC_API_URL=https://chilliguard.dpdns.org

# Model paths inside the container (optional; defaults already work)
MODEL_PATH=./model/chilliscan_cnn.pth
CLASS_NAMES_PATH=./model/class_names.json
MAX_UPLOAD_MB=10
```

Notes:
- Do **not** duplicate keys (e.g. only one `DATABASE_URL`).
- For Google OAuth, the redirect URI must be `https://chilliguard.dpdns.org/api/auth/callback/google` (adjust domain if different).
- If you accidentally exposed any secrets, rotate them (DB password, Gemini key, NextAuth secret, Google client secret).
