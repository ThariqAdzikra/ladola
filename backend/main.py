"""
ChilliGuard backend API.

Serves a trained MobileNetV2 model for chili disease detection.
"""

from __future__ import annotations

import io
import json
import os
import re
import time
import traceback
from pathlib import Path
from typing import Any
from contextlib import asynccontextmanager

# Third-party imports
# pyrefly: ignore [missing-import]
import torch
# pyrefly: ignore [missing-import]
import torch.nn as nn
# pyrefly: ignore [missing-import]
from torchvision import models as tv_models, transforms
# pyrefly: ignore [missing-import]
from PIL import Image
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, File, HTTPException, UploadFile, Depends
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
import google.generativeai as genai
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

# Local imports
from database import Base, database_url_safe, engine, engine_error, get_db
from models import User, Scan, ChatSession, Message


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DEFAULT_MODEL_DIR = BASE_DIR / "model"

# Load environment variables from multiple possible locations
load_dotenv(BASE_DIR / ".env")
load_dotenv(REPO_ROOT / ".env")

def _env_path(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    if not raw:
        return default
    value = Path(raw)
    return value if value.is_absolute() else (BASE_DIR / value).resolve()


def _parse_origins(value: str | None) -> list[str]:
    default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    if not value:
        return default_origins
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def _parse_gemini_models(primary: str, fallbacks: str | None) -> list[str]:
    model_names = [primary.strip()]
    if fallbacks:
        model_names.extend(model.strip() for model in fallbacks.split(",") if model.strip())

    deduped: list[str] = []
    for model_name in model_names:
        if model_name and model_name not in deduped:
            deduped.append(model_name)
    return deduped


MODEL_PATH = _env_path("MODEL_PATH", DEFAULT_MODEL_DIR / "chilliscan_cnn.pth")
CLASS_NAMES_PATH = _env_path("CLASS_NAMES_PATH", DEFAULT_MODEL_DIR / "class_names.json")
ALLOWED_ORIGINS = _parse_origins(os.getenv("ALLOWED_ORIGINS"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
GEMINI_MODEL_NAMES = _parse_gemini_models(
    GEMINI_MODEL_NAME,
    os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash"),
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Configure Gemini
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
    print(f"[info] Gemini AI configured with models: {', '.join(GEMINI_MODEL_NAMES)}")
else:
    print("[warn] GOOGLE_API_KEY or GEMINI_API_KEY not found in environment")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    print(f"[info] Starting ChilliGuard API on {DEVICE.type}")
    try:
        load_model()
    except Exception as exc:
        print(f"[critical] Failed to load model during startup: {exc}")

    if engine is not None:
        try:
            Base.metadata.create_all(bind=engine)
            print("[info] Database tables ensured")
        except Exception as exc:
            print(f"[critical] Failed to initialize database schema: {exc}")
    yield
    print("[info] Shutting down ChilliGuard API")

app = FastAPI(
    title="ChilliGuard API",
    description="Chili disease detection powered by a CNN model",
    version="1.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


CLASS_DISPLAY_NAMES = {
    "chilli_anthracnos": "Antraknosa",
    "chilli_damping_off": "Layu Fusarium",
    "chilli_healthy_fruit": "Sehat (Buah)",
    "chilli_healthy_leaf": "Sehat (Daun)",
    "chilli_leaf_curl_virus": "Virus Keriting Daun",
    "chilli_leaf_spot": "Bercak Daun",
    "chilli_veinal_mottle_virus": "Virus Mottle Vena",
    "chilli_whitefly": "Kutu Kebul",
    "chilli_yellowish": "Menguning",
}

DISEASE_INFO: dict[str, dict[str, Any]] = {
    "Antraknosa": {
        "disease_id": 1,
        "label_en": "Anthracnose",
        "severity": "parah",
        "type": "fruit",
        "description": "Penyakit jamur yang disebabkan oleh Colletotrichum spp. Ditandai dengan lesi gelap dan cekung pada buah.",
        "symptoms": [
            "Bercak hitam cekung pada buah",
            "Buah membusuk dari ujung",
            "Spora berwarna oranye atau merah muda pada lesi",
            "Buah menjadi keriput and mengering",
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
            "Hindari penyiraman dari atas",
            "Rotasi tanaman setiap musim tanam",
        ],
    },
    "Virus Keriting Daun": {
        "disease_id": 2,
        "label_en": "Leaf Curl Virus",
        "severity": "parah",
        "type": "leaf",
        "description": "Penyakit viral yang ditularkan oleh kutu kebul dan menyebabkan daun menggulung serta pertumbuhan terhambat.",
        "symptoms": [
            "Daun menggulung ke atas",
            "Pertumbuhan tanaman terhambat",
            "Daun menguning dan mengecil",
            "Buah sedikit dan kecil",
        ],
        "treatment": [
            "Cabut dan musnahkan tanaman yang terinfeksi berat",
            "Kendalikan populasi kutu kebul dengan insektisida",
            "Pasang perangkap kuning",
            "Gunakan mulsa plastik perak untuk mengusir kutu kebul",
        ],
        "prevention": [
            "Gunakan bibit yang bebas virus",
            "Tanam tanaman penghalang",
            "Jaga kebersihan lahan dari gulma",
            "Gunakan jaring serangga",
        ],
    },
    "Bercak Daun": {
        "disease_id": 3,
        "label_en": "Leaf Spot",
        "severity": "ringan",
        "type": "leaf",
        "description": "Bercak daun yang muncul sebagai lesi coklat atau hitam dengan tepi kekuningan.",
        "symptoms": [
            "Bercak coklat atau hitam pada daun",
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
        "description": "Hama kutu kebul yang mengisap cairan tanaman dan menjadi vektor virus.",
        "symptoms": [
            "Kutu putih kecil di bawah daun",
            "Daun menguning dan layu",
            "Terdapat embun madu pada daun",
            "Jamur jelaga hitam tumbuh pada embun madu",
        ],
        "treatment": [
            "Semprot insektisida imidakloprid atau abamektin",
            "Gunakan sabun insektisida",
            "Pasang yellow sticky trap di sekitar tanaman",
            "Lepas predator alami seperti Encarsia formosa",
        ],
        "prevention": [
            "Tanam trap crop di pinggir lahan",
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
        "description": "Penyakit layu akibat jamur Fusarium yang menyerang akar dan pangkal batang tanaman.",
        "symptoms": [
            "Tanaman layu mendadak",
            "Batang bawah berwarna coklat",
            "Akar membusuk",
            "Tanaman mati dalam beberapa hari",
        ],
        "treatment": [
            "Cabut tanaman yang terinfeksi beserta akarnya",
            "Aplikasikan Trichoderma atau fungisida tanah",
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
        "description": "Daun menguning karena defisiensi nutrisi atau stres lingkungan.",
        "symptoms": [
            "Daun menguning merata atau dari tepi",
            "Pertumbuhan lambat",
            "Buah kecil dan sedikit",
            "Daun tua gugur lebih cepat",
        ],
        "treatment": [
            "Berikan pupuk NPK seimbang",
            "Tambahkan pupuk daun yang mengandung magnesium dan besi",
            "Perbaiki pH tanah bila terlalu asam atau basa",
            "Pastikan penyiraman cukup dan teratur",
        ],
        "prevention": [
            "Lakukan pemupukan rutin sesuai jadwal",
            "Tes tanah sebelum tanam",
            "Gunakan pupuk organik untuk memperbaiki struktur tanah",
            "Jaga kelembaban tanah yang konsisten",
        ],
    },
    "Virus Mottle Vena": {
        "disease_id": 7,
        "label_en": "Veinal Mottle Virus",
        "severity": "parah",
        "type": "leaf",
        "description": "Virus yang menyerang pembuluh daun cabai dan menyebabkan pola mosaik pada tulang daun.",
        "symptoms": [
            "Pola mosaik hijau tua dan muda pada tulang daun",
            "Daun mengkerut dan bergelombang",
            "Pertumbuhan terhambat",
            "Produksi buah menurun drastis",
        ],
        "treatment": [
            "Tidak ada obat untuk virus, cabut tanaman terinfeksi",
            "Kendalikan serangga vektor seperti kutu daun",
            "Musnahkan tanaman yang terinfeksi berat",
            "Disinfeksi alat setelah menangani tanaman sakit",
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
        "description": "Tidak ada penyakit terdeteksi. Buah cabai tampak sehat dan normal.",
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
        "description": "Tidak ada penyakit terdeteksi. Daun cabai tampak sehat dan normal.",
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

model: nn.Module | None = None
class_info: dict[str, Any] | None = None
metadata_source = "missing"
model_load_error: str | None = None

preprocess = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)

# --- Pydantic Schemas ---

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


class ChatRequest(BaseModel):
    message: str
    prediction_context: dict[str, Any]
    history: list[dict[str, str]] = []

class ChatResponse(BaseModel):
    text: str

class MessageCreate(BaseModel):
    sender: str
    text: str
    scan_id: int | None = None


class ScanCreate(BaseModel):

    user_email: str
    image_url: str
    disease_label: str
    confidence: float
    severity: str

class ChatSessionCreate(BaseModel):
    user_email: str
    scan_id: int | None = None
    title: str
    messages: list[MessageCreate] = []

class UserSyncRequest(BaseModel):
    email: str
    name: str
    avatar_url: str | None = None


class IntegratedSaveRequest(BaseModel):
    user_email: str
    image_url: str
    disease_label: str
    confidence: float
    severity: str
    session_id: int | None = None # Existing session to append to
    title: str | None = None # New session title
    intro_text: str | None = None # Initial AI message text

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


# --- Helper Functions ---

def _load_state_dict(path: Path) -> dict[str, torch.Tensor]:
    try:
        return torch.load(path, map_location=DEVICE, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=DEVICE)


def _infer_num_classes(state_dict: dict[str, torch.Tensor]) -> int:
    classifier_weight = state_dict.get("classifier.1.weight")
    if classifier_weight is None:
        raise RuntimeError("Unable to infer class count from model weights.")
    return int(classifier_weight.shape[0])


def _build_fallback_class_info(expected_num_classes: int | None = None) -> dict[str, Any]:
    class_names_raw = sorted(CLASS_DISPLAY_NAMES)
    class_names = [CLASS_DISPLAY_NAMES.get(name, name) for name in class_names_raw]
    if expected_num_classes is not None and len(class_names) != expected_num_classes:
        raise RuntimeError(
            "Model output classes do not match fallback metadata. "
            f"Expected {expected_num_classes}, found {len(class_names)}."
        )
    metadata = {
        name: {
            "label_en": DISEASE_INFO.get(name, {}).get("label_en", name),
            "severity": DISEASE_INFO.get(name, {}).get("severity", "ringan"),
            "disease_id": DISEASE_INFO.get(name, {}).get("disease_id", 0),
        }
        for name in class_names
    }
    return {
        "class_names": class_names,
        "class_names_raw": class_names_raw,
        "metadata": metadata,
        "num_classes": len(class_names),
    }


def _load_class_info(expected_num_classes: int) -> tuple[dict[str, Any], str]:
    if CLASS_NAMES_PATH.exists():
        with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as handle:
            info = json.load(handle)
        if len(info.get("class_names", [])) != expected_num_classes:
            raise RuntimeError(
                "class_names.json does not match the trained model output size."
            )
        info.setdefault("num_classes", len(info["class_names"]))
        info.setdefault("metadata", {})
        return info, "file"
    return _build_fallback_class_info(expected_num_classes), "fallback"


def _create_model(num_classes: int) -> nn.Module:
    network = tv_models.mobilenet_v2(weights=None)
    network.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(network.last_channel, num_classes),
    )
    network.to(DEVICE)
    network.eval()
    return network


def _is_gemini_quota_error(exc: Exception) -> bool:
    error_text = f"{type(exc).__name__}: {exc}".lower()
    return any(
        token in error_text
        for token in (
            "429",
            "quota",
            "rate limit",
            "rate-limits",
            "resourceexhausted",
            "resource exhausted",
            "too many requests",
        )
    )


def _extract_retry_delay_seconds(error_text: str) -> int | None:
    retry_match = re.search(r"retry in\s+([\d.]+)s", error_text, re.IGNORECASE)
    if retry_match:
        try:
            return max(1, round(float(retry_match.group(1))))
        except ValueError:
            return None

    delay_match = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", error_text, re.IGNORECASE)
    if delay_match:
        return int(delay_match.group(1))
    return None


def _format_steps(items: list[Any]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def _offline_chat_response(request: ChatRequest, notice: str) -> ChatResponse:
    p = request.prediction_context or {}
    label = p.get("label", "hasil diagnosis")
    question = request.message.lower()
    symptoms = p.get("symptoms") or []
    treatment = p.get("treatment") or []
    prevention = p.get("prevention") or []

    if any(keyword in question for keyword in ("gejala", "tanda", "awal", "waspada")) and symptoms:
        body = f"Gejala yang perlu diperhatikan pada {label}:\n{_format_steps(symptoms)}"
    elif any(keyword in question for keyword in ("cegah", "pencegahan", "hindari", "kembali")) and prevention:
        body = f"Pencegahan yang disarankan untuk {label}:\n{_format_steps(prevention)}"
    elif any(keyword in question for keyword in ("obat", "obati", "penanganan", "fungisida", "pestisida", "semprot", "dosis")) and treatment:
        body = f"Langkah penanganan awal untuk {label}:\n{_format_steps(treatment)}"
    else:
        sections = [f"Berdasarkan hasil scan, tanaman terdeteksi {label}."]
        if p.get("description"):
            sections.append(str(p["description"]))
        if treatment:
            sections.append(f"Penanganan utama:\n{_format_steps(treatment[:3])}")
        if prevention:
            sections.append(f"Pencegahan lanjutan:\n{_format_steps(prevention[:3])}")
        body = "\n\n".join(sections)

    return ChatResponse(text=f"{notice}\n\n{body}")


def load_model() -> None:
    global model, class_info, metadata_source, model_load_error

    model = None
    class_info = None
    metadata_source = "missing"
    model_load_error = None

    if not MODEL_PATH.exists():
        model_load_error = f"Model file not found: {MODEL_PATH}"
        print(f"[warn] {model_load_error}")
        return

    try:
        print(f"[info] Loading model from {MODEL_PATH}")
        state_dict = _load_state_dict(MODEL_PATH)
        num_classes = _infer_num_classes(state_dict)
        class_info, metadata_source = _load_class_info(num_classes)

        network = _create_model(num_classes)
        network.load_state_dict(state_dict)
        model = network

        print(
            "[info] Model loaded successfully "
            f"(classes={num_classes}, source={metadata_source}, device={DEVICE.type})"
        )
    except Exception as exc:
        model_load_error = str(exc)
        print(f"[error] Failed to load model: {exc}")
        traceback.print_exc()


def predict_image(image_bytes: bytes) -> PredictionResult:
    if model is None or class_info is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Train the model or provide the model artifact first.",
        )

    start = time.perf_counter()

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid image file: {exc}") from exc

    input_tensor = preprocess(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]

    class_names = class_info["class_names"]
    scores = probabilities.cpu().tolist()
    ranked_indices = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
    top_index = ranked_indices[0]
    top_label = class_names[top_index]
    top_score = float(scores[top_index])
    info = DISEASE_INFO.get(top_label, {})

    return PredictionResult(
        disease_id=info.get("disease_id", 0),
        label=top_label,
        label_en=info.get("label_en", top_label),
        confidence=round(top_score, 4),
        severity=info.get("severity", "ringan"),
        type=info.get("type", "leaf"),
        description=info.get("description", ""),
        symptoms=info.get("symptoms", []),
        treatment=info.get("treatment", []),
        prevention=info.get("prevention", []),
        all_scores=[
            ScoreItem(label=class_names[index], score=round(float(scores[index]), 4))
            for index in ranked_indices
        ],
        inference_time_ms=round((time.perf_counter() - start) * 1000, 2),
    )


# --- API Endpoints ---

@app.get("/", tags=["Health"])
async def root() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "ChilliGuard API",
        "model_loaded": model is not None,
        "model_error": model_load_error,
        "database_ready": engine is not None,
        "database_error": engine_error,
        "num_classes": class_info["num_classes"] if class_info else 0,
        "metadata_source": metadata_source,
    }


@app.get("/health", tags=["Health"])
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_error": model_load_error,
        "database_ready": engine is not None,
        "database_url": database_url_safe,
        "database_error": engine_error,
        "model_path": str(MODEL_PATH),
        "class_info_path": str(CLASS_NAMES_PATH),
        "num_classes": class_info["num_classes"] if class_info else 0,
        "metadata_source": metadata_source,
        "allowed_origins": ALLOWED_ORIGINS,
    }

@app.post("/api/users/sync", tags=["Users"])
def sync_user(req: UserSyncRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(email=req.email, name=req.name, avatar_url=req.avatar_url, password_hash="sso")
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.name != req.name or user.avatar_url != req.avatar_url:
        user.name = req.name
        user.avatar_url = req.avatar_url
        db.commit()
        db.refresh(user)
    return {"id": user.id, "email": user.email}


@app.post("/predict", response_model=PredictionResult, tags=["Detection"])
async def predict(file: UploadFile = File(...)) -> PredictionResult:
    allowed_types = {"image/bmp", "image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported media type '{file.content_type}'. "
                f"Allowed: {', '.join(sorted(allowed_types))}"
            ),
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        max_size_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"File too large. Max {max_size_mb} MB.")

    # --- GUARDRAIL: Verify if it's a chilli plant/leaf ---
    if GENAI_API_KEY:
        try:
            print(f"[debug] Running guardrail for file: {file.filename} ({file.content_type})")
            guardrail_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            image_part = {"mime_type": file.content_type, "data": contents}
            prompt = (
                "Identify all main objects in this image. "
                "If there is a person, human, face, or part of a human, respond with 'HUMAN'. "
                "If it is clearly a chilli plant, chilli leaf, or chilli fruit, respond with 'CHILLI'. "
                "If it is neither, or if it is a random object, respond with 'OTHER'. "
                "Be very strict: if you see a human, you MUST respond 'HUMAN'."
            )
            response = guardrail_model.generate_content([prompt, image_part])
            decision = response.text.strip().upper()
            print(f"[debug] Guardrail raw response: '{decision}'")
            
            # Rejection logic: must contain CHILLI and must NOT contain HUMAN
            if "HUMAN" in decision or "CHILLI" not in decision:
                print(f"[debug] Guardrail REJECTED the image. Reason: {decision}")
                return PredictionResult(
                    disease_id=-1,
                    label="Bukan Tanaman Cabai",
                    label_en="Not a Chilli Plant",
                    confidence=1.0,
                    severity="peringatan",
                    type="none",
                    description=f"Deteksi dibatalkan. ChilliGuard mendeteksi objek non-cabai ({decision.lower()}).",
                    symptoms=[],
                    treatment=[],
                    prevention=[
                        "Jangan arahkan kamera ke wajah atau orang lain.",
                        "Pastikan objek utama foto adalah daun atau buah cabai.",
                        "ChilliGuard hanya berfungsi untuk mendiagnosis tanaman cabai."
                    ],
                    all_scores=[],
                    inference_time_ms=0.0
                )
            print("[debug] Guardrail PASSED the image")
        except Exception as e:
            print(f"[error] Guardrail error: {e}")
            traceback.print_exc()

    return predict_image(contents)


@app.post("/chat", response_model=ChatResponse, tags=["AI"])
async def chat(request: ChatRequest) -> ChatResponse:
    if not GENAI_API_KEY:
        return _offline_chat_response(
            request,
            "Mode offline: Gemini API belum dikonfigurasi di server, jadi jawaban memakai data hasil diagnosis ChilliGuard.",
        )

    try:
        p = request.prediction_context
        # Create a clean history for Gemini
        gemini_history = []
        
        # Add messages from request.history, ensuring alternating roles
        last_role = None
        for msg in request.history:
            if not msg.get("text") or not msg.get("text").strip():
                continue
            
            # Gemini roles must be 'user' or 'model'
            role = "user" if msg["role"] == "user" else "model"
            
            # Gemini doesn't allow two consecutive messages from the same role
            if role == last_role:
                if gemini_history:
                    gemini_history[-1]["parts"][0] += f"\n\n{msg['text']}"
                continue
            
            gemini_history.append({"role": role, "parts": [msg["text"]]})
            last_role = role

        # Gemini history MUST start with a 'user' message
        if gemini_history and gemini_history[0]["role"] == "model":
            gemini_history.insert(0, {"role": "user", "parts": ["Halo, saya butuh bantuan dengan hasil diagnosis cabai saya."]})
        
        # Contextual prompt for the current question
        context_prompt = (
            f"Konteks Deteksi Tanaman Cabai:\n"
            f"Penyakit: {p.get('label', 'Tidak diketahui')}\n"
            f"Deskripsi: {p.get('description', '')}\n\n"
            f"Pertanyaan Pengguna: {request.message}"
        )

        system_instruction = (
            "Anda adalah ChilliGuard AI, asisten khusus diagnosis penyakit tanaman cabai. "
            "STRICT RULES:\n"
            "1. HANYA jawab pertanyaan seputar tanaman cabai, penyakit cabai, dan perawatan cabai.\n"
            "2. JANGAN PERNAH memberikan kode pemrograman (coding), skrip, atau instruksi teknis komputer.\n"
            "3. Jika ditanya di luar konteks cabai (misal: resep masakan umum, politik, matematika, koding), "
            "jawablah dengan: 'Maaf, saya hanya bisa membantu pertanyaan seputar kesehatan tanaman cabai.'\n"
            "4. Jawab dalam bahasa Indonesia yang ramah dan profesional."
        )

        for index, model_name in enumerate(GEMINI_MODEL_NAMES):
            try:
                print(f"[debug] Sending chat request with Gemini model: {model_name}")
                gemini_model = genai.GenerativeModel(
                    model_name,
                    system_instruction=system_instruction,
                )
                chat_session = gemini_model.start_chat(history=gemini_history)
                response = chat_session.send_message(context_prompt)

                if not response or not response.text:
                    return ChatResponse(text="Maaf, saya tidak mendapatkan jawaban dari AI. Coba tanya lagi?")

                return ChatResponse(text=response.text)
            except Exception as exc:
                has_next_model = index < len(GEMINI_MODEL_NAMES) - 1
                if _is_gemini_quota_error(exc) and has_next_model:
                    next_model = GEMINI_MODEL_NAMES[index + 1]
                    print(f"[warn] Gemini model quota/rate limit hit: {model_name}. Trying fallback: {next_model}")
                    continue
                raise

    except Exception as exc:
        if _is_gemini_quota_error(exc):
            print(f"\n[warn] All Gemini models reached quota/rate limit: {exc}")
            traceback.print_exc()
            retry_seconds = _extract_retry_delay_seconds(str(exc))
            retry_note = f" Coba akses Gemini lagi sekitar {retry_seconds} detik lagi." if retry_seconds else ""
            return _offline_chat_response(
                request,
                f"Mode offline: semua model Gemini sedang terkena kuota atau rate limit.{retry_note} Jawaban berikut memakai data hasil diagnosis ChilliGuard.",
            )

        print(f"\n[CRITICAL] Gemini API Error: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail={
                "code": "AI_PROVIDER_ERROR",
                "message": "Layanan AI sedang tidak dapat dihubungi. Silakan coba lagi nanti.",
            },
        )

@app.get("/diseases", response_model=list[DiseaseInfo], tags=["Info"])
async def list_diseases() -> list[DiseaseInfo]:
    return [
        DiseaseInfo(
            disease_id=info["disease_id"],
            label=label,
            label_en=info["label_en"],
            severity=info["severity"],
            type=info["type"],
            description=info["description"],
            symptoms=info["symptoms"],
            treatment=info["treatment"],
            prevention=info["prevention"],
        )
        for label, info in DISEASE_INFO.items()
    ]


# --- Database History Endpoints ---

@app.post("/api/history/integrated-save", tags=["History"])
def integrated_save(req: IntegratedSaveRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {req.user_email} not found")
    
    # 1. Create Scan
    new_scan = Scan(
        user_id=user.id,
        image_url=req.image_url,
        disease_label=req.disease_label,
        confidence=req.confidence,
        severity=req.severity
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    # 2. Handle Session
    session_id = req.session_id
    if not session_id or session_id == 0:
        # Create new session
        new_session = ChatSession(
            user_id=user.id,
            scan_id=new_scan.id,
            title=req.title or req.disease_label
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id
    else:
        # Verify existing session
        target_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not target_session:
            # Fallback: create new
            new_session = ChatSession(
                user_id=user.id,
                scan_id=new_scan.id,
                title=req.title or req.disease_label
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            session_id = new_session.id

    # 3. Create Message (Intro from AI)
    if req.intro_text:
        new_msg = Message(
            session_id=session_id,
            sender="system", # Ensure it's identified as a diagnosis card
            text=req.intro_text,
            scan_id=new_scan.id
        )
        db.add(new_msg)
        db.commit()

    return {
        "status": "ok",
        "session_id": session_id,
        "scan_id": new_scan.id
    }

@app.post("/api/scans", tags=["History"])
def create_scan(req: ScanCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {req.user_email} not found")
    
    new_scan = Scan(
        user_id=user.id,
        image_url=req.image_url,
        disease_label=req.disease_label,
        confidence=req.confidence,
        severity=req.severity
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    return {"id": new_scan.id}

@app.post("/api/chat-sessions", tags=["History"])
def create_session(req: ChatSessionCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {req.user_email} not found")
    
    new_session = ChatSession(
        user_id=user.id,
        scan_id=req.scan_id,
        title=req.title
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    for msg in req.messages:
        db_msg = Message(
            session_id=new_session.id,
            sender=msg.sender,
            text=msg.text,
            scan_id=msg.scan_id
        )
        db.add(db_msg)
    
    db.commit()
    return {"id": new_session.id}

@app.get("/api/chat-sessions", tags=["History"])
def list_sessions(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return []
    
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(ChatSession.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "scan_id": s.scan_id,
            "diagnosis": s.title
        } for s in sessions
    ]

@app.get("/api/chat-sessions/{session_id}", tags=["History"])
def get_session(session_id: int, db: Session = Depends(get_db)):
    target_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not target_session:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {session_id} not found")
    
    messages = db.query(Message).filter(Message.session_id == target_session.id).order_by(Message.created_at.asc()).all()
    
    formatted_messages = []
    for m in messages:
        msg_data = {
            "role": "user" if m.sender == "user" else "assistant" if m.sender == "ai" else "system",
            "text": m.text,
            "created_at": m.created_at.isoformat()
        }
        
        if m.scan_id:
            scan = db.query(Scan).filter(Scan.id == m.scan_id).first()
            if scan:
                info = DISEASE_INFO.get(scan.disease_label, {})
                msg_data["prediction"] = {
                    "label": scan.disease_label,
                    "confidence": float(scan.confidence),
                    "severity": scan.severity,
                    "image_url": scan.image_url,
                    **info
                }
                msg_data["image"] = scan.image_url
        
        formatted_messages.append(msg_data)

    return {
        "id": target_session.id,
        "title": target_session.title,
        "messages": formatted_messages
    }

@app.post("/api/chat-sessions/{session_id}/messages", tags=["History"])
def add_message(session_id: int, req: MessageCreate, db: Session = Depends(get_db)):
    target_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not target_session:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {session_id} not found")
    
    new_msg = Message(
        session_id=session_id,
        sender=req.sender,
        text=req.text,
        scan_id=req.scan_id
    )
    db.add(new_msg)
    db.commit()
    return {"status": "ok", "id": new_msg.id}

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("APP_ENV") != "production",
    )
