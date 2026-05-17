"""
Train a MobileNetV2 classifier for the ChilliGuard dataset.

Outputs:
    model/chilliscan_cnn.pth
    model/class_names.json
    model/training_history.png
    model/training_metrics.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset, Subset, WeightedRandomSampler
from torchvision import datasets, models, transforms


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


@dataclass
class TrainingConfig:
    dataset_dir: Path
    model_dir: Path
    img_size: int = 224
    batch_size: int = 32
    epochs: int = 25
    freeze_epochs: int = 10
    learning_rate: float = 1e-3
    fine_tune_lr: float = 1e-5
    val_split: float = 0.2
    early_stop_patience: int = 5
    num_workers: int = 0
    seed: int = 42

    @property
    def model_path(self) -> Path:
        return self.model_dir / "chilliscan_cnn.pth"

    @property
    def class_names_path(self) -> Path:
        return self.model_dir / "class_names.json"

    @property
    def history_plot_path(self) -> Path:
        return self.model_dir / "training_history.png"

    @property
    def metrics_path(self) -> Path:
        return self.model_dir / "training_metrics.json"


class TransformDataset(Dataset):
    def __init__(self, subset: Subset, transform: transforms.Compose):
        self.subset = subset
        self.transform = transform

    def __len__(self) -> int:
        return len(self.subset)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        image, label = self.subset[index]
        if self.transform:
            image = self.transform(image)
        return image, label


def build_arg_parser() -> argparse.ArgumentParser:
    repo_root = Path(__file__).resolve().parent.parent
    default_workers = 0 if os.name == "nt" else min(4, os.cpu_count() or 1)

    parser = argparse.ArgumentParser(description="Train the ChilliGuard CNN model.")
    parser.add_argument("--dataset-dir", type=Path, default=repo_root / "Dataset")
    parser.add_argument("--model-dir", type=Path, default=Path(__file__).resolve().parent / "model")
    parser.add_argument("--img-size", type=int, default=224)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--freeze-epochs", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--fine-tune-lr", type=float, default=1e-5)
    parser.add_argument("--val-split", type=float, default=0.2)
    parser.add_argument("--early-stop-patience", type=int, default=5)
    parser.add_argument("--num-workers", type=int, default=default_workers)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def parse_config() -> TrainingConfig:
    args = build_arg_parser().parse_args()
    return TrainingConfig(
        dataset_dir=args.dataset_dir.resolve(),
        model_dir=args.model_dir.resolve(),
        img_size=args.img_size,
        batch_size=args.batch_size,
        epochs=args.epochs,
        freeze_epochs=args.freeze_epochs,
        learning_rate=args.learning_rate,
        fine_tune_lr=args.fine_tune_lr,
        val_split=args.val_split,
        early_stop_patience=args.early_stop_patience,
        num_workers=args.num_workers,
        seed=args.seed,
    )


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_transforms(img_size: int) -> tuple[transforms.Compose, transforms.Compose]:
    train_transforms = transforms.Compose(
        [
            transforms.RandomResizedCrop(img_size, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(p=0.2),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    val_transforms = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(img_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    return train_transforms, val_transforms


def validate_dataset(config: TrainingConfig) -> None:
    if not config.dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {config.dataset_dir}")
    folders = [path for path in config.dataset_dir.iterdir() if path.is_dir()]
    if not folders:
        raise FileNotFoundError(f"No class folders found in dataset: {config.dataset_dir}")


def create_datasets(
    config: TrainingConfig,
) -> tuple[Dataset, Dataset, WeightedRandomSampler, list[str], list[str], np.ndarray]:
    full_dataset = datasets.ImageFolder(str(config.dataset_dir))
    class_names_raw = full_dataset.classes
    class_names = [CLASS_DISPLAY_NAMES.get(name, name) for name in class_names_raw]
    targets = np.array(full_dataset.targets)
    indices = np.arange(len(full_dataset))

    train_idx, val_idx = train_test_split(
        indices,
        test_size=config.val_split,
        stratify=targets,
        random_state=config.seed,
    )

    train_transforms, val_transforms = build_transforms(config.img_size)
    train_subset = TransformDataset(Subset(full_dataset, train_idx.tolist()), train_transforms)
    val_subset = TransformDataset(Subset(full_dataset, val_idx.tolist()), val_transforms)

    train_targets = targets[train_idx]
    class_counts = np.bincount(train_targets, minlength=len(class_names))
    class_weights = 1.0 / (class_counts + 1e-6)
    sample_weights = [float(class_weights[label]) for label in train_targets]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

    print("\nDataset summary")
    print(f"  Total images : {len(full_dataset)}")
    print(f"  Train split  : {len(train_idx)}")
    print(f"  Val split    : {len(val_idx)}")
    print("  Classes")
    for index, (name, count) in enumerate(zip(class_names, class_counts, strict=False)):
        print(f"    [{index}] {name:<24} train={int(count):>4} weight={class_weights[index]:.5f}")

    return train_subset, val_subset, sampler, class_names, class_names_raw, class_counts


def create_data_loaders(
    train_dataset: Dataset,
    val_dataset: Dataset,
    sampler: WeightedRandomSampler,
    config: TrainingConfig,
) -> tuple[DataLoader, DataLoader]:
    common = {
        "batch_size": config.batch_size,
        "num_workers": config.num_workers,
        "pin_memory": torch.cuda.is_available(),
        "persistent_workers": config.num_workers > 0,
    }
    train_loader = DataLoader(train_dataset, sampler=sampler, **common)
    val_loader = DataLoader(val_dataset, shuffle=False, **common)
    return train_loader, val_loader


def create_model(num_classes: int, device: torch.device) -> nn.Module:
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    for param in model.features.parameters():
        param.requires_grad = False
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(model.last_channel, num_classes),
    )
    return model.to(device)


def unfreeze_top_layers(model: nn.Module, num_layers: int = 5) -> None:
    for layer in list(model.features.children())[-num_layers:]:
        for param in layer.parameters():
            param.requires_grad = True


def load_state_dict(path: Path, device: torch.device) -> dict[str, torch.Tensor]:
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return running_loss / max(total, 1), correct / max(total, 1)


def validate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, list[int], list[int]]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            all_preds.extend(predicted.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    return running_loss / max(total, 1), correct / max(total, 1), all_preds, all_labels


def plot_history(history: dict[str, list[float]], save_path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    epochs = range(1, len(history["train_loss"]) + 1)

    ax1.plot(epochs, history["train_loss"], "b-o", label="Train loss", markersize=3)
    ax1.plot(epochs, history["val_loss"], "r-o", label="Val loss", markersize=3)
    ax1.set_title("Loss")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.plot(epochs, history["train_acc"], "b-o", label="Train acc", markersize=3)
    ax2.plot(epochs, history["val_acc"], "r-o", label="Val acc", markersize=3)
    ax2.set_title("Accuracy")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved training curve to {save_path}")


def save_class_info(
    config: TrainingConfig,
    class_names: list[str],
    class_names_raw: list[str],
    best_val_accuracy: float,
) -> None:
    payload = {
        "class_names": class_names,
        "class_names_raw": class_names_raw,
        "metadata": {name: CLASS_METADATA.get(name, {}) for name in class_names},
        "num_classes": len(class_names),
        "img_size": config.img_size,
        "best_val_accuracy": round(best_val_accuracy, 4),
    }
    with open(config.class_names_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Saved class metadata to {config.class_names_path}")


def save_metrics(
    config: TrainingConfig,
    history: dict[str, list[float]],
    class_names: list[str],
    class_counts: np.ndarray,
    best_val_accuracy: float,
    final_val_accuracy: float,
    report: dict[str, Any],
    matrix: np.ndarray,
) -> None:
    payload = {
        "config": {
            **asdict(config),
            "dataset_dir": str(config.dataset_dir),
            "model_dir": str(config.model_dir),
        },
        "class_names": class_names,
        "class_counts": [int(value) for value in class_counts.tolist()],
        "best_val_accuracy": round(best_val_accuracy, 4),
        "final_val_accuracy": round(final_val_accuracy, 4),
        "history": {key: [round(float(item), 6) for item in values] for key, values in history.items()},
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
    }
    with open(config.metrics_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Saved training metrics to {config.metrics_path}")


def run_training(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    scheduler: optim.lr_scheduler.ReduceLROnPlateau,
    config: TrainingConfig,
    device: torch.device,
    phase_label: str,
    start_epoch: int,
    total_epochs: int,
    history: dict[str, list[float]],
    best_val_accuracy: float,
) -> tuple[float, int]:
    patience_counter = 0

    print(f"\n{phase_label}")
    print("-" * len(phase_label))

    for epoch in range(start_epoch, total_epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, _, _ = validate(model, val_loader, criterion, device)
        scheduler.step(val_loss)
        elapsed = time.time() - t0

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print(
            f"Epoch {epoch:02d}/{total_epochs} | "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} | "
            f"{elapsed:.1f}s"
        )

        if val_acc > best_val_accuracy:
            best_val_accuracy = val_acc
            torch.save(model.state_dict(), config.model_path)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= config.early_stop_patience:
                print(f"Early stopping triggered at epoch {epoch}.")
                return best_val_accuracy, epoch

    return best_val_accuracy, total_epochs


def main() -> None:
    config = parse_config()
    validate_dataset(config)
    config.model_dir.mkdir(parents=True, exist_ok=True)
    seed_everything(config.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 60)
    print("ChilliGuard CNN Training")
    print("=" * 60)
    print(f"Device      : {device}")
    print(f"Dataset dir : {config.dataset_dir}")
    print(f"Model dir   : {config.model_dir}")

    train_dataset, val_dataset, sampler, class_names, class_names_raw, class_counts = create_datasets(config)
    train_loader, val_loader = create_data_loaders(train_dataset, val_dataset, sampler, config)

    model = create_model(len(class_names), device)
    criterion = nn.CrossEntropyLoss()
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    best_val_accuracy = 0.0

    phase1_epochs = min(max(config.freeze_epochs, 0), config.epochs)
    if phase1_epochs > 0:
        optimizer = optim.Adam(model.classifier.parameters(), lr=config.learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
        best_val_accuracy, _ = run_training(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            criterion=criterion,
            optimizer=optimizer,
            scheduler=scheduler,
            config=config,
            device=device,
            phase_label="Phase 1 - train classifier head",
            start_epoch=1,
            total_epochs=phase1_epochs,
            history=history,
            best_val_accuracy=best_val_accuracy,
        )

    remaining_epochs = max(config.epochs - phase1_epochs, 0)
    if remaining_epochs > 0 and config.model_path.exists():
        model.load_state_dict(load_state_dict(config.model_path, device))
        unfreeze_top_layers(model, num_layers=5)
        optimizer = optim.Adam(
            [
                {"params": model.features.parameters(), "lr": config.fine_tune_lr},
                {"params": model.classifier.parameters(), "lr": config.fine_tune_lr * 10},
            ]
        )
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
        best_val_accuracy, _ = run_training(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            criterion=criterion,
            optimizer=optimizer,
            scheduler=scheduler,
            config=config,
            device=device,
            phase_label="Phase 2 - fine tune top feature layers",
            start_epoch=phase1_epochs + 1,
            total_epochs=config.epochs,
            history=history,
            best_val_accuracy=best_val_accuracy,
        )

    if not config.model_path.exists():
        raise RuntimeError("Training finished without producing a model checkpoint.")

    model.load_state_dict(load_state_dict(config.model_path, device))
    _, final_val_accuracy, all_preds, all_labels = validate(model, val_loader, criterion, device)

    report_text = classification_report(all_labels, all_preds, target_names=class_names, zero_division=0)
    report_dict = classification_report(
        all_labels,
        all_preds,
        target_names=class_names,
        zero_division=0,
        output_dict=True,
    )
    matrix = confusion_matrix(all_labels, all_preds)

    print("\nBest validation accuracy :", f"{best_val_accuracy:.4f}")
    print("Final validation accuracy:", f"{final_val_accuracy:.4f}")
    print("\nClassification report")
    print(report_text)

    save_class_info(config, class_names, class_names_raw, best_val_accuracy)
    plot_history(history, config.history_plot_path)
    save_metrics(
        config=config,
        history=history,
        class_names=class_names,
        class_counts=class_counts,
        best_val_accuracy=best_val_accuracy,
        final_val_accuracy=final_val_accuracy,
        report=report_dict,
        matrix=matrix,
    )

    print(f"\nModel saved to {config.model_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
