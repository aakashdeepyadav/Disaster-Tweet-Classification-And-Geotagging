"""
Configuration file for model training and hyperparameter tuning.
All hyperparameters and model settings are centralized here.
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ModelConfig:
    """Configuration for a single model"""
    name: str
    model_path: str
    tokenizer_path: str
    max_length: int
    batch_size: int
    learning_rate: float
    epochs: int
    warmup_steps: int
    weight_decay: float
    dropout: float = 0.1

@dataclass
class TrainingConfig:
    """Global training configuration"""
    # Data settings
    train_csv_path: str = "train.csv"
    test_size: float = 0.2
    validation_size: float = 0.1
    random_seed: int = 42
    stratify_split: bool = True
    
    # Cross-validation
    use_cross_validation: bool = False
    cv_folds: int = 5
    
    # Model selection
    compare_models: bool = True
    save_best_model: bool = True
    best_model_metric: str = "f1_score"  # Options: accuracy, f1_score, precision, recall
    
    # Training settings
    device: str = "auto"  # "auto", "cuda", "cpu"
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    early_stopping_patience: int = 3
    early_stopping_min_delta: float = 0.001
    
    # Logging and saving
    save_dir: str = "models"
    log_dir: str = "logs"
    save_checkpoints: bool = True
    checkpoint_frequency: int = 1  # Save checkpoint every N epochs
    
    # Evaluation
    evaluation_metrics: List[str] = None
    
    def __post_init__(self):
        if self.evaluation_metrics is None:
            self.evaluation_metrics = ["accuracy", "f1_score", "precision", "recall", "roc_auc"]

# Model configurations to compare
MODEL_CONFIGS = [
    ModelConfig(
        name="distilbert-base-uncased",
        model_path="distilbert-base-uncased",
        tokenizer_path="distilbert-base-uncased",
        max_length=128,
        batch_size=16,
        learning_rate=2e-5,
        epochs=3,
        warmup_steps=0,
        weight_decay=0.01,
    ),
    ModelConfig(
        name="bert-base-uncased",
        model_path="bert-base-uncased",
        tokenizer_path="bert-base-uncased",
        max_length=128,
        batch_size=16,
        learning_rate=2e-5,
        epochs=3,
        warmup_steps=0,
        weight_decay=0.01,
    ),
    ModelConfig(
        name="roberta-base",
        model_path="roberta-base",
        tokenizer_path="roberta-base",
        max_length=128,
        batch_size=16,
        learning_rate=2e-5,
        epochs=3,
        warmup_steps=0,
        weight_decay=0.01,
    ),
]

# Hyperparameter search space for tuning
HYPERPARAMETER_SEARCH_SPACE = {
    "learning_rate": [1e-5, 2e-5, 3e-5, 5e-5],
    "batch_size": [8, 16, 32],
    "max_length": [96, 128, 256],
    "epochs": [3, 4, 5],
    "weight_decay": [0.0, 0.01, 0.1],
    "warmup_steps": [0, 100, 500],
}

# Default training config
DEFAULT_CONFIG = TrainingConfig()













