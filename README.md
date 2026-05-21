# ChilliGuard

ChilliGuard adalah aplikasi web untuk mendeteksi penyakit tanaman cabai dari gambar (CNN) dan menyediakan konsultasi lanjutan via chat AI berbasis konteks hasil diagnosis.

## Kegunaan

- Membantu petani/penyuluh mengidentifikasi penyakit dari foto daun/buah cabai
- Menyediakan ringkasan diagnosis (label, confidence, severity, dan info pendukung)
- Memberi saran/tanya-jawab lanjutan lewat chat AI berbasis konteks hasil scan
- Menyimpan riwayat sesi untuk dilihat ulang

## Struktur Repo

```text
ChilliGuard/
|-- backend/     # FastAPI API + inference PyTorch + DB endpoints
|   |-- model/   # Model terlatih (.pth) + metadata kelas (.json)
`-- frontend/    # Next.js UI + NextAuth (Google OAuth)
```

## Tech Stack

### Frontend (`frontend/`)

- Next.js `16.2.6` (App Router)
- React `19` + TypeScript `5`
- Tailwind CSS `v4` (+ typography)
- NextAuth `v4` (Google OAuth)
- Framer Motion, Lucide Icons
- `react-markdown` + `remark-gfm` (render pesan chat)

### Backend (`backend/`)

- FastAPI + Uvicorn
- PyTorch (CPU) + Torchvision (inference CNN)
- Pillow + NumPy (preprocessing gambar)
- SQLAlchemy + (opsional) Postgres via `psycopg2-binary` (history & user sync)
- Pydantic v2 (schema)
- Integrasi Gemini via `google-generativeai`

### Infra / Deployment

- Single production container: Nginx reverse proxy + FastAPI + Next.js (standalone)
- Multi-stage build: Node (build) + Python (runtime)
- Target deploy: Google Cloud Run (port `8080`)

## Dataset & Kelas Deteksi

Dataset training tidak disertakan di repo produksi untuk mengurangi ukuran. Model sudah dilatih dan disimpan di `backend/model/`.

Model mendeteksi 9 kelas (referensi utama: `backend/model/class_names.json`):

1. Antraknosa (`chilli_anthracnos`)
2. Layu Fusarium (`chilli_damping_off`)
3. Sehat (Buah) (`chilli_healthy_fruit`)
4. Sehat (Daun) (`chilli_healthy_leaf`)
5. Virus Keriting Daun (`chilli_leaf_curl_virus`)
6. Bercak Daun (`chilli_leaf_spot`)
7. Virus Mottle Vena (`chilli_veinal_mottle_virus`)
8. Kutu Kebul (`chilli_whitefly`)
9. Menguning (`chilli_yellowish`)

## Menjalankan Secara Lokal

### Prasyarat

- Node.js >= 22
- Python >= 3.12
- (Opsional) Postgres untuk database production/staging
- (Opsional) Google OAuth credentials untuk login via Google

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --port 8000
```

Backend tersedia di `http://localhost:8000` (healthcheck: `GET /health`).

Catatan database:
- Bila `DATABASE_URL` kosong dan `APP_ENV` bukan `production`, backend akan fallback ke SQLite (`backend/chilliguard.db`).
- Jika DB tidak siap, endpoint yang butuh DB akan mengembalikan `503`.

### Frontend

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Frontend tersedia di `http://localhost:3000`.

## Environment Variables

### Backend (`backend/.env`)

Mulai dari `backend/.env.example`.

- `MODEL_PATH` - path ke model CNN (`.pth`)
- `CLASS_NAMES_PATH` - metadata kelas (`.json`)
- `ALLOWED_ORIGINS` - CORS origins untuk frontend (comma-separated)
- `MAX_UPLOAD_MB` - batas upload (MB)
- `APP_ENV` - `development` atau `production`
- `DATABASE_URL` - koneksi Postgres (opsional di dev; akan fallback SQLite)
- `GEMINI_API_KEY` atau `GOOGLE_API_KEY` - API key Gemini
- `GEMINI_MODEL` - model utama (default di backend: `gemini-2.0-flash-lite` jika env kosong)
- `GEMINI_FALLBACK_MODELS` - fallback model names, dipisah koma

### Frontend (`frontend/.env.local`)

Mulai dari `frontend/.env.example`.

- `NEXT_PUBLIC_API_URL` - base URL backend untuk browser (mis. `http://localhost:8000`)
- `BACKEND_API_URL` - base URL backend untuk server-side (Next.js)
- `NEXTAUTH_URL` - URL publik frontend
- `NEXTAUTH_SECRET` - secret panjang acak
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Google OAuth

## Endpoint Utama (Ringkas)

- `GET /health` - healthcheck backend
- `POST /predict` - inference penyakit dari gambar
- `POST /chat` - chat AI (Gemini) berbasis konteks diagnosis + history
- `GET /diseases` - daftar info penyakit
- `GET /api/chat-sessions?email=...` - list sesi chat
- `GET /api/chat-sessions/{id}` - detail sesi chat + messages
- `POST /api/chat-sessions/{id}/messages` - append message ke sesi

## Deployment (Google Cloud Run)

Deploy production menggunakan root `Dockerfile` (single container: frontend + backend + nginx), diekspos di port `8080`.

### Build & Deploy

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/chilliguard
gcloud run deploy chilliguard \
  --image gcr.io/YOUR_PROJECT_ID/chilliguard \
  --platform managed \
  --port 8080 \
  --allow-unauthenticated
```

### Env Vars (Cloud Run)

Contoh (ganti nilai yang bertanda `<>`):

```env
APP_ENV=production

ALLOWED_ORIGINS=https://<YOUR_DOMAIN>
DATABASE_URL=<your_postgres_url>

# Gemini (backend membaca GOOGLE_API_KEY atau GEMINI_API_KEY)
GEMINI_API_KEY=<your_gemini_api_key>
GEMINI_MODEL=gemini-2.0-flash-lite
GEMINI_FALLBACK_MODELS=gemini-2.5-flash

# NextAuth
NEXTAUTH_URL=https://<YOUR_DOMAIN>
NEXTAUTH_SECRET=<your_random_long_secret>
GOOGLE_CLIENT_ID=<your_google_oauth_client_id>
GOOGLE_CLIENT_SECRET=<your_google_oauth_client_secret>

# Single container: backend tersedia di localhost:8000
BACKEND_API_URL=http://127.0.0.1:8000

# Browser mengarah ke domain publik
NEXT_PUBLIC_API_URL=https://<YOUR_DOMAIN>

MODEL_PATH=./model/chilliscan_cnn.pth
CLASS_NAMES_PATH=./model/class_names.json
MAX_UPLOAD_MB=10
```

Notes:
- Hindari duplikasi key (mis. cukup satu `DATABASE_URL`).
- Redirect URI Google OAuth: `https://<YOUR_DOMAIN>/api/auth/callback/google`.
