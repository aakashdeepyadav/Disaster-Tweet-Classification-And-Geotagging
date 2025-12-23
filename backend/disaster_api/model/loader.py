"""
Smart model loader that automatically finds and loads the best trained model.
Moved from legacy `backend/model_loader.py` into package namespace.
"""
import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional, Tuple, Dict


def find_best_model(models_dir: str = "models") -> Optional[str]:
    """
    Find the best trained model directory.
    Checks for best_model first, then falls back to other models.
    """
    # Priority order
    check_paths = [
        os.path.join(models_dir, "best_model"),
        os.path.join(models_dir, "disaster_model"),
    ]

    # Also check for any model directories (including checkpoints)
    if os.path.exists(models_dir):
        # First, try to find best checkpoint based on metrics
        checkpoint_models = []
        for item in os.listdir(models_dir):
            item_path = os.path.join(models_dir, item)
            if os.path.isdir(item_path) and item not in ["best_model", "disaster_model"]:
                # Check if it's a checkpoint directory
                if "_checkpoint_epoch_" in item:
                    metrics_file = os.path.join(item_path, "metrics.json")
                    if os.path.exists(metrics_file):
                        try:
                            with open(metrics_file, 'r') as f:
                                metrics = json.load(f)
                            checkpoint_models.append((item_path, metrics))
                        except:
                            pass
                elif not item.startswith("_") and not item.endswith("_checkpoint"):
                    check_paths.append(item_path)

        # Sort checkpoints by F1 score (or accuracy if F1 not available)
        if checkpoint_models:
            checkpoint_models.sort(
                key=lambda x: x[1].get("f1_score", x[1].get("accuracy", 0)),
                reverse=True
            )
            # Add best checkpoint to check paths (after best_model but before others)
            check_paths.insert(1, checkpoint_models[0][0])

    # Check each path
    for model_path in check_paths:
        if os.path.exists(model_path):
            # Check if it has required files
            required_files = ["config.json"]
            if all(os.path.exists(os.path.join(model_path, f)) for f in required_files):
                return model_path

    return None


def load_model(model_path: Optional[str] = None, device: str = "auto") -> Tuple:
    """
    Load model and tokenizer from the best available model.
    
    Args:
        model_path: Specific model path, or None to auto-detect
        device: Device to load model on ("auto", "cuda", "cpu")
        
    Returns:
        (model, tokenizer, model_info) tuple
    """
    if model_path is None:
        model_path = find_best_model()

    if model_path is None:
        raise FileNotFoundError(
            "No trained model found! Please run: python train_advanced.py"
        )

    # Determine device
    if device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device)

    print(f"[LOADING] Loading model from: {model_path}")

    # Load tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
    except:
        # Fallback to DistilBERT tokenizer
        from transformers import DistilBertTokenizerFast
        tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)

    # Load model
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()

    # Load model info if available
    info_path = os.path.join(model_path, "training_info.json")
    model_info = {}
    if os.path.exists(info_path):
        with open(info_path, 'r') as f:
            model_info = json.load(f)

    print(f"[SUCCESS] Model loaded successfully!")
    if model_info:
        print(f"   Model: {model_info.get('model_name', 'Unknown')}")
        if 'best_metrics' in model_info:
            metrics = model_info['best_metrics']
            print(f"   Accuracy: {metrics.get('accuracy', 0):.4f}")
            print(f"   F1-Score: {metrics.get('f1_score', 0):.4f}")

    return model, tokenizer, model_info
