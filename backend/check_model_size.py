import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path

MODEL_PATH = Path("backend/model/chilliscan_cnn.pth")

def check_model():
    if not MODEL_PATH.exists():
        print(f"Model file not found at {MODEL_PATH}")
        return

    try:
        state_dict = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    except Exception as e:
        print(f"Error loading state dict: {e}")
        try:
            state_dict = torch.load(MODEL_PATH, map_location="cpu")
        except Exception as e2:
            print(f"Error loading state dict (no weights_only): {e2}")
            return

    classifier_weight = state_dict.get("classifier.1.weight")
    if classifier_weight is not None:
        num_classes = classifier_weight.shape[0]
        print(f"Number of classes in model: {num_classes}")
    else:
        print("Could not find classifier.1.weight in state dict")
        print("Keys in state dict:", state_dict.keys())

if __name__ == "__main__":
    check_model()
