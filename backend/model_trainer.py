"""
Advanced model training with early stopping, checkpointing, and logging.
"""
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from torch.optim import AdamW
from tqdm import tqdm
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
import numpy as np

from config import ModelConfig, TrainingConfig
from evaluation import ModelEvaluator


class AdvancedTrainer:
    """Advanced trainer with early stopping, checkpointing, and logging"""
    
    def __init__(self, model_config: ModelConfig, training_config: TrainingConfig):
        self.model_config = model_config
        self.training_config = training_config
        self.device = self._get_device()
        self.evaluator = ModelEvaluator(save_dir=training_config.log_dir)
        
        # Training history
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "val_metrics": []
        }
        
        # Early stopping
        self.best_val_metric = -float('inf')
        self.early_stopping_counter = 0
        self.best_model_state = None
    
    def _get_device(self):
        """Get the appropriate device"""
        if self.training_config.device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(self.training_config.device)
    
    def _load_model(self):
        """Load model and tokenizer"""
        print(f"\n[Loading] {self.model_config.name}...")
        tokenizer = AutoTokenizer.from_pretrained(self.model_config.tokenizer_path)
        model = AutoModelForSequenceClassification.from_pretrained(
            self.model_config.model_path,
            num_labels=2
        )
        model.to(self.device)
        return model, tokenizer
    
    def _create_optimizer_and_scheduler(self, model, num_training_steps: int):
        """Create optimizer and learning rate scheduler"""
        optimizer = AdamW(
            model.parameters(),
            lr=self.model_config.learning_rate,
            weight_decay=self.model_config.weight_decay
        )
        
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=self.model_config.warmup_steps,
            num_training_steps=num_training_steps
        )
        
        return optimizer, scheduler
    
    def train_epoch(self, model, train_loader, optimizer, scheduler):
        """Train for one epoch with error handling"""
        model.train()
        total_loss = 0
        num_batches = 0
        
        progress_bar = tqdm(train_loader, desc=f"Training {self.model_config.name}")
        
        for batch_idx, batch in enumerate(progress_bar):
            try:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                outputs = model(**batch)
                loss = outputs.loss / self.training_config.gradient_accumulation_steps
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), 
                    self.training_config.max_grad_norm
                )
                
                if (num_batches + 1) % self.training_config.gradient_accumulation_steps == 0:
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                
                total_loss += loss.item() * self.training_config.gradient_accumulation_steps
                num_batches += 1
                
                # Update progress bar
                progress_bar.set_postfix({"loss": f"{loss.item():.4f}"})
                
            except RuntimeError as e:
                if "out of memory" in str(e):
                    print(f"\n[ERROR] GPU out of memory at batch {batch_idx}")
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    raise
                else:
                    print(f"\n[WARNING] Error at batch {batch_idx}: {e}")
                    # Skip this batch and continue
                    optimizer.zero_grad()
                    continue
            except Exception as e:
                print(f"\n[WARNING] Unexpected error at batch {batch_idx}: {e}")
                optimizer.zero_grad()
                continue
        
        if num_batches == 0:
            raise ValueError("No batches were successfully processed!")
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    def validate(self, model, val_loader):
        """Validate model and return metrics"""
        metrics, _ = self.evaluator.evaluate_model(
            model, val_loader, self.device, None
        )
        return metrics
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader) -> Dict:
        """
        Main training loop with early stopping and checkpointing.
        Includes comprehensive error handling to prevent crashes.
        
        Returns:
            Dictionary with training results and best metrics
        """
        model, tokenizer = None, None
        try:
            model, tokenizer = self._load_model()
            
            num_training_steps = len(train_loader) * self.model_config.epochs
            optimizer, scheduler = self._create_optimizer_and_scheduler(model, num_training_steps)
            
            print(f"\n[STARTING] Training for {self.model_config.name}")
            print(f"   Device: {self.device}")
            print(f"   Epochs: {self.model_config.epochs}")
            print(f"   Learning Rate: {self.model_config.learning_rate}")
            print(f"   Batch Size: {self.model_config.batch_size}")
            
            best_metrics = None
            epochs_completed = 0
            
            for epoch in range(1, self.model_config.epochs + 1):
                try:
                    print(f"\n{'='*60}")
                    print(f"Epoch {epoch}/{self.model_config.epochs}")
                    print(f"{'='*60}")
                    
                    # Training with error handling
                    try:
                        train_loss = self.train_epoch(model, train_loader, optimizer, scheduler)
                        self.history["train_loss"].append(train_loss)
                        print(f"Train Loss: {train_loss:.4f}")
                    except Exception as e:
                        print(f"[ERROR] Training failed at epoch {epoch}: {e}")
                        import traceback
                        traceback.print_exc()
                        # Try to continue with next epoch
                        continue
                    
                    # Validation with error handling
                    try:
                        val_metrics = self.validate(model, val_loader)
                        val_loss = 1 - val_metrics.get(self.training_config.best_model_metric, 0)
                        self.history["val_loss"].append(val_loss)
                        self.history["val_metrics"].append(val_metrics)
                        
                        # Print validation metrics
                        self.evaluator.print_evaluation_report(
                            val_metrics, 
                            f"{self.model_config.name} - Epoch {epoch}",
                            detailed=False
                        )
                    except Exception as e:
                        print(f"[ERROR] Validation failed at epoch {epoch}: {e}")
                        import traceback
                        traceback.print_exc()
                        # Use previous metrics if available, otherwise skip
                        if self.history["val_metrics"]:
                            val_metrics = self.history["val_metrics"][-1]
                            print(f"[WARNING] Using previous epoch metrics")
                        else:
                            print(f"[ERROR] No previous metrics available, skipping epoch")
                            continue
                    
                    # Checkpointing with error handling
                    if self.training_config.save_checkpoints and \
                       epoch % self.training_config.checkpoint_frequency == 0:
                        try:
                            self._save_checkpoint(model, tokenizer, epoch, val_metrics)
                        except Exception as e:
                            print(f"[WARNING] Checkpoint saving failed at epoch {epoch}: {e}")
                            # Continue training even if checkpoint fails
                    
                    # Early stopping check (only after epoch 1 to allow initial learning)
                    current_metric = val_metrics.get(self.training_config.best_model_metric, 0)
                    
                    if epoch == 1:
                        # First epoch always sets the baseline
                        self.best_val_metric = current_metric
                        self.early_stopping_counter = 0
                        self.best_model_state = model.state_dict().copy()
                        best_metrics = val_metrics.copy()
                        print(f"[BEST] Initial {self.training_config.best_model_metric}: {current_metric:.4f}")
                    elif current_metric > self.best_val_metric + self.training_config.early_stopping_min_delta:
                        self.best_val_metric = current_metric
                        self.early_stopping_counter = 0
                        self.best_model_state = model.state_dict().copy()
                        best_metrics = val_metrics.copy()
                        print(f"[BEST] New best {self.training_config.best_model_metric}: {current_metric:.4f}")
                    else:
                        self.early_stopping_counter += 1
                        print(f"⏳ No improvement ({self.early_stopping_counter}/{self.training_config.early_stopping_patience})")
                    
                    epochs_completed = epoch
                    
                    # Early stopping (only check after at least 2 epochs)
                    if epoch >= 2 and self.early_stopping_counter >= self.training_config.early_stopping_patience:
                        print(f"\n[EARLY STOP] Early stopping triggered after {epoch} epochs")
                        break
                    
                    # Clear cache to prevent memory issues
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        
                except KeyboardInterrupt:
                    print(f"\n[INTERRUPTED] Training interrupted by user at epoch {epoch}")
                    break
                except Exception as e:
                    print(f"[ERROR] Unexpected error at epoch {epoch}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Try to continue with next epoch
                    continue
            
            # Load best model state
            if self.best_model_state is not None and model is not None:
                try:
                    model.load_state_dict(self.best_model_state)
                    print(f"\n[LOADED] Best model state (metric: {self.best_val_metric:.4f})")
                except Exception as e:
                    print(f"[WARNING] Could not load best model state: {e}")
            
            if best_metrics is None and self.history["val_metrics"]:
                best_metrics = self.history["val_metrics"][-1]
            elif best_metrics is None:
                # Fallback: create dummy metrics
                best_metrics = {"accuracy": 0.0, "f1_score": 0.0}
            
            return {
                "model": model,
                "tokenizer": tokenizer,
                "best_metrics": best_metrics,
                "history": self.history,
                "epochs_trained": epochs_completed
            }
            
        except Exception as e:
            print(f"[CRITICAL ERROR] Training failed completely: {e}")
            import traceback
            traceback.print_exc()
            # Return partial results if available
            return {
                "model": model,
                "tokenizer": tokenizer,
                "best_metrics": best_metrics if 'best_metrics' in locals() else {"accuracy": 0.0},
                "history": self.history,
                "epochs_trained": epochs_completed if 'epochs_completed' in locals() else 0,
                "error": str(e)
            }
    
    def _save_checkpoint(self, model, tokenizer, epoch, metrics):
        """Save model checkpoint with error handling"""
        try:
            checkpoint_dir = os.path.join(
                self.training_config.save_dir,
                f"{self.model_config.name}_checkpoint_epoch_{epoch}"
            )
            os.makedirs(checkpoint_dir, exist_ok=True)
            
            model.save_pretrained(checkpoint_dir)
            tokenizer.save_pretrained(checkpoint_dir)
            
            # Save metrics
            with open(os.path.join(checkpoint_dir, "metrics.json"), 'w') as f:
                json.dump(metrics, f, indent=2)
            
            print(f"[CHECKPOINT] Saved: {checkpoint_dir}")
        except Exception as e:
            print(f"[ERROR] Failed to save checkpoint: {e}")
            raise
    
    def save_model(self, model, tokenizer, metrics: Dict, is_best: bool = False):
        """Save final model"""
        if is_best:
            save_dir = os.path.join(self.training_config.save_dir, "best_model")
        else:
            save_dir = os.path.join(
                self.training_config.save_dir,
                f"{self.model_config.name}_final"
            )
        
        os.makedirs(save_dir, exist_ok=True)
        model.save_pretrained(save_dir)
        tokenizer.save_pretrained(save_dir)
        
        # Save training info
        training_info = {
            "model_name": self.model_config.name,
            "config": {
                "max_length": self.model_config.max_length,
                "batch_size": self.model_config.batch_size,
                "learning_rate": self.model_config.learning_rate,
                "epochs": self.model_config.epochs,
            },
            "best_metrics": metrics,
            "history": self.history,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(os.path.join(save_dir, "training_info.json"), 'w') as f:
            json.dump(training_info, f, indent=2)
        
        print(f"[SAVED] Model saved to: {save_dir}")
        return save_dir

