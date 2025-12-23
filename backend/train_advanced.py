"""
Advanced training script with model comparison, hyperparameter tuning,
and comprehensive evaluation. This is the main entry point for training.
"""
import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import json
from datetime import datetime

from config import MODEL_CONFIGS, DEFAULT_CONFIG, TrainingConfig, ModelConfig
from preprocessing import prepare_training_data
from model_trainer import AdvancedTrainer
from evaluation import ModelEvaluator, ModelComparator


class TweetDataset(Dataset):
    """PyTorch Dataset for tweet classification"""
    def __init__(self, full_texts, labels, tokenizer, max_len=128):
        self.full_texts = full_texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.full_texts)

    def __getitem__(self, idx):
        text = str(self.full_texts[idx])
        enc = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def load_and_prepare_data(config: TrainingConfig):
    """Load and preprocess data"""
    print("="*80)
    print("DATA LOADING AND PREPROCESSING")
    print("="*80)
    
    if not os.path.exists(config.train_csv_path):
        raise FileNotFoundError(
            f"{config.train_csv_path} not found! Please download it from Kaggle."
        )
    
    df = pd.read_csv(config.train_csv_path)
    print(f"Loaded dataset: {len(df)} samples")
    
    # Preprocess
    df = prepare_training_data(df)
    
    return df


def create_data_loaders(df, model_config: ModelConfig, training_config: TrainingConfig):
    """Create train/validation/test data loaders"""
    print("\n" + "="*80)
    print("CREATING DATA LOADERS")
    print("="*80)
    
    # Split into train/val/test
    train_df, temp_df = train_test_split(
        df,
        test_size=training_config.test_size + training_config.validation_size,
        random_state=training_config.random_seed,
        stratify=df["target"] if training_config.stratify_split else None
    )
    
    val_size = training_config.validation_size / (training_config.test_size + training_config.validation_size)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=1 - val_size,
        random_state=training_config.random_seed,
        stratify=temp_df["target"] if training_config.stratify_split else None
    )
    
    print(f"Train set:   {len(train_df)} samples")
    print(f"Val set:     {len(val_df)} samples")
    print(f"Test set:    {len(test_df)} samples")
    
    # For now, we'll use train and val. Test set can be used for final evaluation
    return train_df, val_df, test_df


def train_single_model(model_config: ModelConfig, 
                      train_df: pd.DataFrame,
                      val_df: pd.DataFrame,
                      training_config: TrainingConfig,
                      tokenizer=None):
    """Train a single model"""
    
    # Create datasets
    train_texts = train_df["full_text"].tolist()
    train_labels = train_df["target"].tolist()
    val_texts = val_df["full_text"].tolist()
    val_labels = val_df["target"].tolist()
    
    # Load tokenizer if not provided
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_config.tokenizer_path)
    
    train_dataset = TweetDataset(train_texts, train_labels, tokenizer, model_config.max_length)
    val_dataset = TweetDataset(val_texts, val_labels, tokenizer, model_config.max_length)
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=model_config.batch_size,
        shuffle=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=model_config.batch_size * 2,
        shuffle=False
    )
    
    # Train
    trainer = AdvancedTrainer(model_config, training_config)
    results = trainer.train(train_loader, val_loader)
    
    return results, tokenizer


def check_if_trained(config: TrainingConfig) -> bool:
    """Check if models have already been trained"""
    best_model_path = os.path.join(config.save_dir, "best_model")
    if os.path.exists(best_model_path):
        # Check if model files exist
        model_files = ["config.json", "pytorch_model.bin"]
        if all(os.path.exists(os.path.join(best_model_path, f)) for f in model_files):
            return True
    return False


def compare_models(config: TrainingConfig = None, force_retrain: bool = False):
    """
    Main function to compare multiple models and select the best one.
    
    Args:
        config: Training configuration
        force_retrain: If True, retrain even if model exists
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # Check if already trained
    if not force_retrain and check_if_trained(config):
        print("\n" + "="*80)
        print("[INFO] MODELS ALREADY TRAINED")
        print("="*80)
        print(f"Best model found at: {os.path.join(config.save_dir, 'best_model')}")
        print("\nTo retrain, run with: python train_advanced.py --force")
        print("Or delete the models/ directory and run again.")
        
        # Load best model info
        best_model_path = os.path.join(config.save_dir, "best_model")
        info_path = os.path.join(best_model_path, "training_info.json")
        if os.path.exists(info_path):
            import json
            with open(info_path, 'r') as f:
                info = json.load(f)
            print(f"\n[BEST MODEL] {info.get('model_name', 'Unknown')}")
            print(f"   Best Metrics: {info.get('best_metrics', {})}")
        
        return None, None
    
    # Load and preprocess data
    df = load_and_prepare_data(config)
    
    # Create data splits
    train_df, val_df, test_df = create_data_loaders(df, MODEL_CONFIGS[0], config)
    
    # Initialize comparator
    evaluator = ModelEvaluator(save_dir=config.log_dir)
    comparator = ModelComparator(evaluator)
    
    print("\n" + "="*80)
    print("MODEL COMPARISON")
    print("="*80)
    print(f"Comparing {len(MODEL_CONFIGS)} models...")
    
    best_model_result = None
    best_metric_value = -float('inf')
    
    # Train and evaluate each model
    for i, model_config in enumerate(MODEL_CONFIGS, 1):
        print(f"\n{'#'*80}")
        print(f"MODEL {i}/{len(MODEL_CONFIGS)}: {model_config.name}")
        print(f"{'#'*80}")
        
        model = None
        tokenizer = None
        try:
            # Clear GPU cache before training new model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Train model
            results, tokenizer = train_single_model(
                model_config, train_df, val_df, config
            )
            
            # Get best metrics
            best_metrics = results.get("best_metrics", {})
            
            # Check if training actually completed
            epochs_trained = results.get("epochs_trained", 0)
            if epochs_trained == 0:
                print(f"[WARNING] {model_config.name} did not complete any epochs. Skipping.")
                continue
            
            if "error" in results:
                print(f"[WARNING] {model_config.name} had errors during training: {results['error']}")
                # Still try to use partial results if available
            
            # Add to comparator
            comparator.add_model_result(
                model_config.name,
                best_metrics,
                {
                    "max_length": model_config.max_length,
                    "batch_size": model_config.batch_size,
                    "learning_rate": model_config.learning_rate,
                    "epochs": model_config.epochs,
                    "epochs_completed": epochs_trained,
                }
            )
            
            # Check if this is the best model
            current_metric = best_metrics.get(config.best_model_metric, 0)
            if current_metric > best_metric_value:
                best_metric_value = current_metric
                best_model_result = {
                    "model": results["model"],
                    "tokenizer": tokenizer,
                    "config": model_config,
                    "metrics": best_metrics
                }
            
            # Save evaluation results
            try:
                evaluator.save_evaluation_results(
                    best_metrics,
                    model_config.name,
                    {
                        "max_length": model_config.max_length,
                        "batch_size": model_config.batch_size,
                        "learning_rate": model_config.learning_rate,
                    }
                )
            except Exception as e:
                print(f"[WARNING] Failed to save evaluation results: {e}")
            
            # Clear model from memory (keep tokenizer for best model)
            model = results.get("model")
            if model is not None and model_config.name != best_model_result.get("config", {}).get("name") if best_model_result else True:
                del model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
        except KeyboardInterrupt:
            print(f"\n[INTERRUPTED] Training interrupted by user")
            print(f"   Completed {i-1}/{len(MODEL_CONFIGS)} models")
            break
        except Exception as e:
            print(f"[ERROR] Error training {model_config.name}: {e}")
            import traceback
            traceback.print_exc()
            # Clear memory and continue
            if model is not None:
                del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            continue
    
    # Print comparison
    comparator.print_comparison(config.best_model_metric)
    comparator.save_comparison()
    
    # Save best model
    if best_model_result and config.save_best_model:
        try:
            print(f"\n{'='*80}")
            print("SAVING BEST MODEL")
            print(f"{'='*80}")
            
            trainer = AdvancedTrainer(best_model_result["config"], config)
            save_path = trainer.save_model(
                best_model_result["model"],
                best_model_result["tokenizer"],
                best_model_result["metrics"],
                is_best=True
            )
            
            print(f"\n[SUCCESS] Best model saved to: {save_path}")
            print(f"   Best {config.best_model_metric}: {best_metric_value:.4f}")
            
            # Update app.py to use best model
            try:
                update_app_model_path(save_path)
            except Exception as e:
                print(f"[WARNING] Failed to update app.py: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to save best model: {e}")
            import traceback
            traceback.print_exc()
    
    return best_model_result, comparator


def update_app_model_path(model_path: str):
    """Update app.py to use the best model path"""
    app_path = "app.py"
    if os.path.exists(app_path):
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Update MODEL_DIR - handle both relative and absolute paths
        import re
        # Convert to relative path if needed
        if os.path.isabs(model_path):
            # Make relative to backend directory
            backend_dir = os.path.dirname(os.path.abspath(app_path))
            try:
                model_path = os.path.relpath(model_path, backend_dir)
            except:
                pass
        
        # Escape backslashes for Windows paths in Python strings
        model_path_escaped = model_path.replace('\\', '/')
        
        new_content = re.sub(
            r'MODEL_DIR\s*=\s*["\'][^"\']+["\']',
            f'MODEL_DIR = "{model_path_escaped}"',
            content
        )
        
        with open(app_path, 'w') as f:
            f.write(new_content)
        
        print(f"[SUCCESS] Updated {app_path} to use best model: {model_path_escaped}")


if __name__ == "__main__":
    import torch
    import sys
    
    # Check for force flag
    force_retrain = "--force" in sys.argv or "-f" in sys.argv
    
    print("\n" + "="*80)
    print("ADVANCED DISASTER TWEET CLASSIFICATION - MODEL COMPARISON")
    print("="*80)
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    print("="*80)
    
    # Run model comparison
    best_model, comparator = compare_models(force_retrain=force_retrain)
    
    print("\n" + "="*80)
    if best_model:
        print("TRAINING COMPLETE!")
        print("="*80)
        print(f"[BEST MODEL] {best_model['config'].name}")
        print(f"   Metric ({DEFAULT_CONFIG.best_model_metric}): {best_model['metrics'].get(DEFAULT_CONFIG.best_model_metric, 0):.4f}")
        print(f"\n[SUCCESS] Model ready for deployment!")
        print(f"   Start API with: python app.py")
    else:
        print("MODEL ALREADY TRAINED - READY FOR DEPLOYMENT")
        print("="*80)
        print("[SUCCESS] Best model is already trained and ready to use!")
        print("   Start API with: python app.py")

