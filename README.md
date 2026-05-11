# ChilliGuard 🌶️

> AI-powered chili plant disease detection with post-diagnosis chat interface.

## Monorepo Structure

```
ChilliGuard/
├── frontend/          # Next.js 15 + Tailwind CSS + shadcn/ui
└── backend/           # FastAPI + Python (CNN model serving)
```

---

## Quick Start

### 1. Backend

```bash
cd backend

# Create & activate virtual environment (Python 3.10+)
py -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run dev server
uvicorn main:app --reload --port 8000
```

API docs available at → http://localhost:8000/docs

---

### 2. Frontend

```bash
cd frontend

# Copy env file
cp .env.example .env.local
# → Fill in GEMINI_API_KEY

# Install dependencies
npm install

# Run dev server
npm run dev
```

App available at → http://localhost:3000

---

## Key Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/health` | Health check |
| POST | `/predict` | Upload image → CNN prediction |
| POST | `/api/chat` *(Next.js)* | Proxied Gemini chat |

---

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `MODEL_PATH` | Path to trained `.h5` / `.pt` model file |
| `GEMINI_API_KEY` | Optional — if backend proxies LLM |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | FastAPI base URL (default: `http://localhost:8000`) |
| `GEMINI_API_KEY` | Gemini API key for `/api/chat` route |

---

## Replacing the Mock Model

Open `backend/main.py` and replace `mock_predict()` with your real TensorFlow/PyTorch inference:

```python
def real_predict(image_bytes: bytes) -> PredictionResult:
    img = preprocess(image_bytes)          # resize, normalize
    logits = model.predict(img)            # your CNN
    idx = logits.argmax()
    return PredictionResult(
        label=DISEASE_CATALOGUE[idx]["label"],
        confidence=float(logits[idx]),
        ...
    )
```
