"""
ChilliGuard Backend — FastAPI
Accepts an image upload and returns a mocked CNN disease-detection prediction.
Replace `mock_predict()` with your real TensorFlow/PyTorch inference logic.
"""

import random
import time
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import io

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ChilliGuard API",
    description="Chili plant disease detection powered by CNN",
    version="0.1.0",
)

# Allow the Next.js dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Disease catalogue (will be fed to the LLM as context)
# ---------------------------------------------------------------------------
DISEASE_CATALOGUE = [
    {
        "label": "Anthracnose",
        "type": "fruit",
        "description": (
            "Fungal disease caused by Colletotrichum spp. "
            "Characterized by dark, sunken lesions on fruits."
        ),
    },
    {
        "label": "Leaf Curl Virus",
        "type": "leaf",
        "description": (
            "Viral disease transmitted by whiteflies. "
            "Causes upward or downward curling of leaves."
        ),
    },
    {
        "label": "Powdery Mildew",
        "type": "leaf",
        "description": (
            "Fungal disease that appears as white powdery spots on leaves."
        ),
    },
    {
        "label": "Bacterial Leaf Spot",
        "type": "leaf",
        "description": (
            "Caused by Xanthomonas spp. Presents as water-soaked lesions "
            "that turn brown or black."
        ),
    },
    {
        "label": "Phytophthora Blight",
        "type": "fruit",
        "description": (
            "Caused by Phytophthora capsici. Results in rapid wilting "
            "and dark water-soaked lesions."
        ),
    },
    {
        "label": "Healthy",
        "type": "leaf",
        "description": "No disease detected. The plant appears healthy.",
    },
]

# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------
class PredictionResult(BaseModel):
    label: str
    confidence: float          # 0.0 – 1.0
    disease_type: str          # "leaf" | "fruit"
    description: str
    all_scores: dict[str, float]
    inference_time_ms: float


# ---------------------------------------------------------------------------
# Mock prediction (replace with real model inference)
# ---------------------------------------------------------------------------
def mock_predict(image_bytes: bytes) -> PredictionResult:
    """
    Simulate a CNN forward-pass.
    Replace this function with:
        1. Preprocess image → tensor
        2. model.predict(tensor)
        3. argmax → label + softmax → confidence
    """
    start = time.perf_counter()

    # Validate that it is actually an image
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid image file: {exc}")

    # Simulate inference latency
    time.sleep(random.uniform(0.3, 0.8))

    # Random softmax-like scores across all classes
    raw_scores = [random.random() for _ in DISEASE_CATALOGUE]
    total = sum(raw_scores)
    scores = [s / total for s in raw_scores]

    best_idx = scores.index(max(scores))
    disease = DISEASE_CATALOGUE[best_idx]

    inference_ms = (time.perf_counter() - start) * 1000

    return PredictionResult(
        label=disease["label"],
        confidence=round(scores[best_idx], 4),
        disease_type=disease["type"],
        description=disease["description"],
        all_scores={
            DISEASE_CATALOGUE[i]["label"]: round(scores[i], 4)
            for i in range(len(DISEASE_CATALOGUE))
        },
        inference_time_ms=round(inference_ms, 2),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "ChilliGuard API"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictionResult, tags=["Detection"])
async def predict(file: UploadFile = File(...)):
    """
    Upload a chili leaf / fruit image.
    Returns the predicted disease class and confidence score.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type '{file.content_type}'. "
                   f"Allowed: {', '.join(allowed_types)}",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10 MB guard
        raise HTTPException(status_code=413, detail="File too large. Max 10 MB.")

    return mock_predict(contents)
