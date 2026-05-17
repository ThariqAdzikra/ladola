# ChilliGuard

AI-powered chili disease detection with a CNN backend and a Next.js frontend.

## Structure

```text
ChilliGuard/
|-- Dataset/    # ImageFolder-style training dataset
|-- backend/    # FastAPI API + PyTorch training and inference
`-- frontend/   # Next.js app
```

## Dataset classes

The current dataset contains 9 classes:

1. `chilli_anthracnos`
2. `chilli_damping_off`
3. `chilli_healthy_fruit`
4. `chilli_healthy_leaf`
5. `chilli_leaf_curl_virus`
6. `chilli_leaf_spot`
7. `chilli_veinal_mottle_virus`
8. `chilli_whitefly`
9. `chilli_yellowish`

## Backend setup

```powershell
cd D:\ChilliGuard\backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the API:

```powershell
uvicorn main:app --reload --port 8000
```

Important endpoints:

- `GET /health`
- `POST /predict`
- `GET /diseases`

## Train or retrain the CNN

From `D:\ChilliGuard\backend`:

```powershell
.\venv\Scripts\Activate.ps1
python train_model.py
```

Useful optional flags:

```powershell
python train_model.py --epochs 15 --batch-size 16 --num-workers 0
```

Training will generate:

- `backend/model/chilliscan_cnn.pth`
- `backend/model/class_names.json`
- `backend/model/training_history.png`
- `backend/model/training_metrics.json`

## Frontend setup

```powershell
cd D:\ChilliGuard\frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Set these values in `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_API_URL=http://127.0.0.1:8000
```

The web app now uses Next.js API routes as a proxy for the FastAPI backend:

- `POST /api/predict` -> FastAPI `POST /predict`
- `GET /api/health` -> FastAPI `GET /health`

That means the browser no longer calls the Python API directly, so local web usage is more reliable and does not depend on client-side CORS setup.
