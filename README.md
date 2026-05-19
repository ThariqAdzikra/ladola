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

Set these in the Cloud Run service configuration:

- `APP_ENV`: `production`
- `ALLOWED_ORIGINS`: `https://chilliguard.dpdns.org`
- `DATABASE_URL`: (Use Neon or Cloud SQL URL)
- `GOOGLE_API_KEY`: (Your Gemini API Key)
- `NEXTAUTH_URL`: `https://chilliguard.dpdns.org`
- `NEXTAUTH_SECRET`: (Random string)
- `GOOGLE_CLIENT_ID`: (For Google Auth)
- `GOOGLE_CLIENT_SECRET`: (For Google Auth)
- `NEXT_PUBLIC_API_URL`: `https://chilliguard.dpdns.org`
