"""
ChilliScan — CNN Training Script
=================================
Trains a MobileNetV2 (transfer learning) on the chilli disease dataset.

Usage:
    source venv/bin/activate
    python train_model.py

Output:
    model/chilliscan_cnn.pth    — Trained model weights
    model/class_names.json      — Index → class name mapping
    model/training_history.png  — Loss & accuracy curves
"""

import json
import os
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, models, transforms
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATASET_DIR = Path(__file__).parent.parent / "Dataset"
MODEL_DIR = Path(__file__).parent / "model"
MODEL_PATH = MODEL_DIR / "chilliscan_cnn.pth"
CLASS_NAMES_PATH = MODEL_DIR / "class_names.json"
HISTORY_PLOT_PATH = MODEL_DIR / "training_history.png"

IMG_SIZE = 224
BATCH_SIZE = 32
NUM_EPOCHS = 25
LEARNING_RATE = 1e-3
FINE_TUNE_LR = 1e-5
EARLY_STOP_PATIENCE = 5
NUM_WORKERS = 4
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Human-readable class name mapping (folder name → display name)
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

# Metadata for each class (maps to frontend DISEASES array)
CLASS_METADATA = {
    "Antraknosa": {"label_en": "Anthracnose", "severity": "parah", "disease_id": 1},
    "Layu Fusarium": {"label_en": "Damping Off", "severity": "parah", "disease_id": 5},
    "Sehat (Buah)": {"label_en": "Healthy Fruit", "severity": "sehat", "disease_id": 8},
    "Sehat (Daun)": {"label_en": "Healthy Leaf", "severity": "sehat", "disease_id": 8},
    "Virus Keriting Daun": {"label_en": "Leaf Curl Virus", "severity": "parah", "disease_id": 2},
    "Bercak Daun": {"label_en": "Leaf Spot", "severity": "ringan", "disease_id": 3},
    "Virus Mottle Vena": {"label_en": "Veinal Mottle Virus", "severity": "parah", "disease_id": 7},
    "Kutu Kebul": {"label_en": "Whitefly", "severity": "ringan", "disease_id": 4},
    "Menguning": {"label_en": "Yellowish", "severity": "ringan", "disease_id": 6},
}


# ---------------------------------------------------------------------------
# Data Transforms
# ---------------------------------------------------------------------------
train_transforms = transforms.Compose([
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

val_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# ---------------------------------------------------------------------------
# Dataset Setup with Stratified Split
# ---------------------------------------------------------------------------
def create_datasets():
    """Create train/val datasets with stratified split."""
    full_dataset = datasets.ImageFolder(str(DATASET_DIR))
    class_names_raw = full_dataset.classes  # folder names sorted
    
    # Map folder names to display names
    class_names = [CLASS_DISPLAY_NAMES.get(name, name) for name in class_names_raw]
    
    targets = full_dataset.targets
    indices = list(range(len(full_dataset)))
    
    train_idx, val_idx = train_test_split(
        indices, test_size=0.2, stratify=targets, random_state=42
    )
    
    # Create subsets
    train_dataset = torch.utils.data.Subset(full_dataset, train_idx)
    val_dataset = torch.utils.data.Subset(full_dataset, val_idx)
    
    # Apply transforms via wrapper
    train_dataset = TransformDataset(train_dataset, train_transforms)
    val_dataset = TransformDataset(val_dataset, val_transforms)
    
    # Compute class weights for WeightedRandomSampler
    train_targets = [targets[i] for i in train_idx]
    class_counts = np.bincount(train_targets, minlength=len(class_names))
    class_weights = 1.0 / (class_counts + 1e-6)
    sample_weights = [class_weights[t] for t in train_targets]
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )
    
    print(f"\n📊 Dataset Summary:")
    print(f"   Total images: {len(full_dataset)}")
    print(f"   Training: {len(train_idx)} | Validation: {len(val_idx)}")
    print(f"\n   Class distribution:")
    for i, (name, count) in enumerate(zip(class_names, class_counts)):
        print(f"   [{i}] {name:25s} → {count:5d} train samples (weight: {class_weights[i]:.4f})")
    
    return train_dataset, val_dataset, sampler, class_names, class_names_raw


class TransformDataset(torch.utils.data.Dataset):
    """Wrapper to apply transforms to a Subset."""
    def __init__(self, subset, transform):
        self.subset = subset
        self.transform = transform
    
    def __len__(self):
        return len(self.subset)
    
    def __getitem__(self, idx):
        img, label = self.subset[idx]
        if self.transform:
            img = self.transform(img)
        return img, label


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def create_model(num_classes: int) -> nn.Module:
    """Create MobileNetV2 with custom classification head."""
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    
    # Freeze base layers
    for param in model.features.parameters():
        param.requires_grad = False
    
    # Replace classifier
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(model.last_channel, num_classes),
    )
    
    return model.to(DEVICE)


def unfreeze_top_layers(model: nn.Module, num_layers: int = 5):
    """Unfreeze the last N feature layers for fine-tuning."""
    layers = list(model.features.children())
    for layer in layers[-num_layers:]:
        for param in layer.parameters():
            param.requires_grad = True


# ---------------------------------------------------------------------------
# Training Loop
# ---------------------------------------------------------------------------
def train_one_epoch(model, dataloader, criterion, optimizer):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, labels in dataloader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
    
    return running_loss / total, correct / total


def validate(model, dataloader, criterion):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in dataloader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    return running_loss / total, correct / total, all_preds, all_labels


def plot_history(history: dict, save_path: Path):
    """Plot training/validation loss and accuracy curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    epochs = range(1, len(history["train_loss"]) + 1)
    
    ax1.plot(epochs, history["train_loss"], "b-o", label="Train Loss", markersize=3)
    ax1.plot(epochs, history["val_loss"], "r-o", label="Val Loss", markersize=3)
    ax1.set_title("Loss", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(epochs, history["train_acc"], "b-o", label="Train Acc", markersize=3)
    ax2.plot(epochs, history["val_acc"], "r-o", label="Val Acc", markersize=3)
    ax2.set_title("Accuracy", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n📈 Training plot saved to {save_path}")


# ---------------------------------------------------------------------------
# Main Training Flow
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("🌶️  ChilliScan — CNN Training")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"Dataset: {DATASET_DIR}")
    
    # Create output dir
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    train_dataset, val_dataset, sampler, class_names, class_names_raw = create_datasets()
    num_classes = len(class_names)
    
    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, sampler=sampler,
        num_workers=NUM_WORKERS, pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=True,
    )
    
    # Create model
    model = create_model(num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=2
    )
    
    # Training history
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    best_val_acc = 0.0
    patience_counter = 0
    
    # ---- Phase 1: Train classifier head (frozen base) ----
    print(f"\n{'='*60}")
    print("📌 Phase 1: Training classifier head (base frozen)")
    print(f"{'='*60}")
    
    phase1_epochs = min(10, NUM_EPOCHS // 2)
    for epoch in range(1, phase1_epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc, _, _ = validate(model, val_loader, criterion)
        scheduler.step(val_loss)
        elapsed = time.time() - t0
        
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        
        print(
            f"  Epoch {epoch:2d}/{phase1_epochs} | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
            f"{elapsed:.1f}s"
        )
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), MODEL_PATH)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOP_PATIENCE:
                print(f"  ⚠️ Early stopping at epoch {epoch}")
                break
    
    # ---- Phase 2: Fine-tune top layers ----
    print(f"\n{'='*60}")
    print("🔧 Phase 2: Fine-tuning top layers")
    print(f"{'='*60}")
    
    # Load best model from phase 1
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
    unfreeze_top_layers(model, num_layers=5)
    
    # Lower learning rate for fine-tuning
    optimizer = optim.Adam([
        {"params": model.features.parameters(), "lr": FINE_TUNE_LR},
        {"params": model.classifier.parameters(), "lr": FINE_TUNE_LR * 10},
    ])
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=2
    )
    patience_counter = 0
    
    remaining_epochs = NUM_EPOCHS - phase1_epochs
    for epoch in range(1, remaining_epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc, _, _ = validate(model, val_loader, criterion)
        scheduler.step(val_loss)
        elapsed = time.time() - t0
        
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        
        print(
            f"  Epoch {epoch:2d}/{remaining_epochs} | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
            f"{elapsed:.1f}s"
        )
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), MODEL_PATH)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOP_PATIENCE:
                print(f"  ⚠️ Early stopping at epoch {epoch}")
                break
    
    # ---- Final Evaluation ----
    print(f"\n{'='*60}")
    print("📊 Final Evaluation")
    print(f"{'='*60}")
    
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
    _, final_acc, all_preds, all_labels = validate(model, val_loader, criterion)
    
    print(f"\n✅ Best Validation Accuracy: {best_val_acc:.4f} ({best_val_acc*100:.1f}%)")
    print(f"\nClassification Report:")
    print(classification_report(all_labels, all_preds, target_names=class_names))
    
    # Save class names
    class_info = {
        "class_names": class_names,
        "class_names_raw": class_names_raw,
        "metadata": CLASS_METADATA,
        "num_classes": num_classes,
        "img_size": IMG_SIZE,
        "best_val_accuracy": round(best_val_acc, 4),
    }
    with open(CLASS_NAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(class_info, f, ensure_ascii=False, indent=2)
    print(f"📄 Class names saved to {CLASS_NAMES_PATH}")
    
    # Plot history
    plot_history(history, HISTORY_PLOT_PATH)
    
    print(f"\n🎉 Model saved to {MODEL_PATH}")
    print(f"   File size: {MODEL_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
