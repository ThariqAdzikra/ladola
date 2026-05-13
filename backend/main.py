"""
ChilliScan Backend — FastAPI
=============================
Real CNN inference for chilli plant disease detection.
"""

import io
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ChilliScan API",
    description="Chili plant disease detection powered by CNN (MobileNetV2)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
MODEL_DIR = Path(__file__).parent / "model"
MODEL_PATH = MODEL_DIR / "chilliscan_cnn.pth"
CLASS_NAMES_PATH = MODEL_DIR / "class_names.json"

DEVICE = torch.device("cpu")
model = None
class_info = None
preprocess = None


def load_model():
    """Load trained CNN model and class info."""
    global model, class_info, preprocess

    if not MODEL_PATH.exists():
        print(f"⚠️  Model not found at {MODEL_PATH}. Running in mock mode.")
        return

    # Load class info
    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
        class_info = json.load(f)

    num_classes = class_info["num_classes"]

    # Build model architecture (must match training)
    model = models.mobilenet_v2(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(model.last_channel, num_classes),
    )

    # Load weights
    state_dict = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()

    # Preprocessing pipeline (must match training val_transforms)
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    print(f"✅ Model loaded: {num_classes} classes, {MODEL_PATH.stat().st_size / 1024 / 1024:.1f} MB")


@app.on_event("startup")
async def startup_event():
    load_model()


# ---------------------------------------------------------------------------
# Disease knowledge base (matches frontend mock-data.ts DISEASES array)
# ---------------------------------------------------------------------------
DISEASE_INFO = {
    "Antraknosa": {
        "disease_id": 1,
        "label_en": "Anthracnose",
        "severity": "parah",
        "type": "fruit",
        "description": "Penyakit jamur yang disebabkan oleh Colletotrichum spp. Ditandai dengan lesi gelap dan cekung pada buah.",
        "symptoms": [
            "Bercak hitam cekung pada buah",
            "Buah membusuk dari ujung",
            "Spora berwarna oranye/merah muda pada lesi",
            "Buah menjadi keriput dan mengering",
        ],
        "treatment": [
            "Buang buah yang terinfeksi segera",
            "Aplikasikan fungisida berbahan aktif mankozeb",
            "Semprot dengan interval 7-10 hari saat musim hujan",
            "Gunakan mulsa untuk mencegah percikan air tanah ke buah",
        ],
        "prevention": [
            "Pilih varietas yang tahan antraknosa",
            "Jaga jarak tanam yang cukup untuk sirkulasi udara",
            "Hindari penyiraman dari atas (overhead irrigation)",
            "Rotasi tanaman setiap musim tanam",
        ],
    },
    "Virus Keriting Daun": {
        "disease_id": 2,
        "label_en": "Leaf Curl Virus",
        "severity": "parah",
        "type": "leaf",
        "description": "Penyakit viral yang ditularkan oleh kutu kebul (whitefly). Menyebabkan daun menggulung ke atas atau ke bawah.",
        "symptoms": [
            "Daun menggulung ke atas",
            "Pertumbuhan tanaman terhambat",
            "Daun menguning dan mengecil",
            "Buah sedikit dan kecil",
        ],
        "treatment": [
            "Cabut dan musnahkan tanaman yang terinfeksi berat",
            "Kendalikan populasi kutu kebul dengan insektisida",
            "Pasang perangkap kuning (yellow sticky trap)",
            "Gunakan mulsa plastik perak untuk mengusir kutu kebul",
        ],
        "prevention": [
            "Gunakan bibit yang bebas virus",
            "Tanam tanaman penghalang (barrier crop)",
            "Jaga kebersihan lahan dari gulma",
            "Gunakan jaring serangga (insect net)",
        ],
    },
    "Bercak Daun": {
        "disease_id": 3,
        "label_en": "Leaf Spot",
        "severity": "ringan",
        "type": "leaf",
        "description": "Disebabkan oleh Xanthomonas spp. Muncul sebagai lesi basah yang berubah coklat atau hitam.",
        "symptoms": [
            "Bercak coklat/hitam pada daun",
            "Lesi berbentuk bulat dengan tepi kuning",
            "Daun menguning secara bertahap",
            "Daun yang parah akan gugur",
        ],
        "treatment": [
            "Aplikasikan bakterisida tembaga",
            "Buang daun yang terinfeksi",
            "Kurangi kelembaban dengan jarak tanam lebih lebar",
            "Semprot secara berkala setiap 7 hari",
        ],
        "prevention": [
            "Hindari menyiram tanaman dari atas",
            "Gunakan drip irrigation",
            "Sanitasi alat-alat pertanian",
            "Rotasi tanaman minimal 2 tahun",
        ],
    },
    "Kutu Kebul": {
        "disease_id": 4,
        "label_en": "Whitefly",
        "severity": "ringan",
        "type": "leaf",
        "description": "Hama kutu kebul (Bemisia tabaci) yang mengisap cairan tanaman dan menjadi vektor virus.",
        "symptoms": [
            "Kutu putih kecil di bawah daun",
            "Daun menguning dan layu",
            "Terdapat embun madu (honeydew) pada daun",
            "Jamur jelaga hitam tumbuh pada embun madu",
        ],
        "treatment": [
            "Semprot insektisida imidakloprid atau abamektin",
            "Gunakan sabun insektisida",
            "Pasang yellow sticky trap di sekitar tanaman",
            "Lepas predator alami seperti Encarsia formosa",
        ],
        "prevention": [
            "Tanam tanaman perangkap (trap crop) di pinggir lahan",
            "Gunakan mulsa plastik perak",
            "Jaga kebersihan lahan dari gulma inang",
            "Monitor populasi secara rutin",
        ],
    },
    "Layu Fusarium": {
        "disease_id": 5,
        "label_en": "Damping Off",
        "severity": "parah",
        "type": "leaf",
        "description": "Penyakit layu yang disebabkan oleh jamur Fusarium. Menyerang sistem perakaran dan batang tanaman.",
        "symptoms": [
            "Tanaman layu mendadak",
            "Batang bawah berwarna coklat",
            "Akar membusuk",
            "Tanaman mati dalam beberapa hari",
        ],
        "treatment": [
            "Cabut tanaman yang terinfeksi beserta akarnya",
            "Aplikasikan fungisida trichoderma pada tanah",
            "Perbaiki drainase tanah",
            "Lakukan solarisasi tanah sebelum tanam ulang",
        ],
        "prevention": [
            "Gunakan media tanam steril",
            "Aplikasi Trichoderma secara preventif",
            "Jaga pH tanah 6.0-6.5",
            "Hindari genangan air",
        ],
    },
    "Menguning": {
        "disease_id": 6,
        "label_en": "Yellowish",
        "severity": "ringan",
        "type": "leaf",
        "description": "Daun menguning karena defisiensi nutrisi atau stres lingkungan. Bukan penyakit patogen langsung.",
        "symptoms": [
            "Daun menguning merata atau dari tepi",
            "Pertumbuhan lambat",
            "Buah kecil dan sedikit",
            "Daun tua gugur lebih cepat",
        ],
        "treatment": [
            "Berikan pupuk NPK seimbang",
            "Tambahkan pupuk daun mengandung magnesium dan besi",
            "Perbaiki pH tanah jika terlalu asam/basa",
            "Pastikan penyiraman cukup dan teratur",
        ],
        "prevention": [
            "Lakukan pemupukan rutin sesuai jadwal",
            "Tes tanah sebelum tanam untuk mengetahui kebutuhan nutrisi",
            "Gunakan pupuk organik untuk memperbaiki struktur tanah",
            "Jaga kelembaban tanah yang konsisten",
        ],
    },
    "Virus Mottle Vena": {
        "disease_id": 7,
        "label_en": "Veinal Mottle Virus",
        "severity": "parah",
        "type": "leaf",
        "description": "Virus yang menyerang pembuluh daun cabai, menyebabkan pola mosaik pada tulang daun.",
        "symptoms": [
            "Pola mosaik hijau tua-muda pada tulang daun",
            "Daun mengkerut dan bergelombang",
            "Pertumbuhan terhambat",
            "Produksi buah menurun drastis",
        ],
        "treatment": [
            "Tidak ada obat untuk virus — cabut tanaman terinfeksi",
            "Kendalikan serangga vektor (kutu daun)",
            "Musnahkan tanaman yang terinfeksi dengan dibakar",
            "Disinfeksi alat pertanian setelah menangani tanaman sakit",
        ],
        "prevention": [
            "Gunakan bibit bersertifikat bebas virus",
            "Kendalikan populasi kutu daun sejak dini",
            "Tanam varietas tahan virus jika tersedia",
            "Sanitasi lahan sebelum musim tanam baru",
        ],
    },
    "Sehat (Buah)": {
        "disease_id": 8,
        "label_en": "Healthy Fruit",
        "severity": "sehat",
        "type": "fruit",
        "description": "Tidak ada penyakit terdeteksi. Buah cabai terlihat sehat dan normal.",
        "symptoms": [],
        "treatment": [],
        "prevention": [
            "Lanjutkan perawatan rutin",
            "Pemupukan sesuai jadwal",
            "Monitor tanaman secara berkala",
            "Jaga kebersihan lahan",
        ],
    },
    "Sehat (Daun)": {
        "disease_id": 8,
        "label_en": "Healthy Leaf",
        "severity": "sehat",
        "type": "leaf",
        "description": "Tidak ada penyakit terdeteksi. Daun cabai terlihat sehat dan normal.",
        "symptoms": [],
        "treatment": [],
        "prevention": [
            "Lanjutkan perawatan rutin",
            "Pemupukan sesuai jadwal",
            "Monitor tanaman secara berkala",
            "Jaga kebersihan lahan",
        ],
    },
}


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class ScoreItem(BaseModel):
    label: str
    score: float


class PredictionResult(BaseModel):
    disease_id: int
    label: str
    label_en: str
    confidence: float
    severity: str
    type: str
    description: str
    symptoms: list[str]
    treatment: list[str]
    prevention: list[str]
    all_scores: list[ScoreItem]
    inference_time_ms: float


class DiseaseInfo(BaseModel):
    disease_id: int
    label: str
    label_en: str
    severity: str
    type: str
    description: str
    symptoms: list[str]
    treatment: list[str]
    prevention: list[str]


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def predict_image(image_bytes: bytes) -> PredictionResult:
    """Run CNN inference on an image."""
    if model is None or class_info is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please train the model first.",
        )

    start = time.perf_counter()

    # Load and preprocess image
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid image file: {exc}")

    input_tensor = preprocess(img).unsqueeze(0).to(DEVICE)

    # Inference
    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]

    inference_ms = (time.perf_counter() - start) * 1000

    # Get predictions
    class_names = class_info["class_names"]
    scores = probabilities.cpu().numpy()

    # Sort by confidence
    sorted_indices = scores.argsort()[::-1]
    all_scores = [
        ScoreItem(label=class_names[i], score=round(float(scores[i]), 4))
        for i in sorted_indices
    ]

    # Top prediction
    top_idx = int(sorted_indices[0])
    top_label = class_names[top_idx]
    top_confidence = float(scores[top_idx])

    # Get disease info
    info = DISEASE_INFO.get(top_label, {})

    return PredictionResult(
        disease_id=info.get("disease_id", 0),
        label=top_label,
        label_en=info.get("label_en", top_label),
        confidence=round(top_confidence, 4),
        severity=info.get("severity", "ringan"),
        type=info.get("type", "leaf"),
        description=info.get("description", ""),
        symptoms=info.get("symptoms", []),
        treatment=info.get("treatment", []),
        prevention=info.get("prevention", []),
        all_scores=all_scores,
        inference_time_ms=round(inference_ms, 2),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "ChilliScan API",
        "model_loaded": model is not None,
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "num_classes": class_info["num_classes"] if class_info else 0,
    }


@app.post("/predict", response_model=PredictionResult, tags=["Detection"])
async def predict(file: UploadFile = File(...)):
    """
    Upload a chili leaf/fruit image.
    Returns the predicted disease class, confidence score, and recommendations.
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

    return predict_image(contents)


@app.get("/diseases", response_model=list[DiseaseInfo], tags=["Info"])
async def list_diseases():
    """Return all detectable diseases with their info."""
    result = []
    seen_ids = set()
    for label, info in DISEASE_INFO.items():
        did = info["disease_id"]
        if did in seen_ids:
            continue
        seen_ids.add(did)
        result.append(
            DiseaseInfo(
                disease_id=did,
                label=label,
                label_en=info["label_en"],
                severity=info["severity"],
                type=info["type"],
                description=info["description"],
                symptoms=info["symptoms"],
                treatment=info["treatment"],
                prevention=info["prevention"],
            )
        )
    return result
