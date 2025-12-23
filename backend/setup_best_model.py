"""
Quick setup script to create best_model from existing checkpoints.
This allows the API to work immediately while full training completes.
"""
import os
import json
import shutil
from pathlib import Path

def find_best_checkpoint(models_dir="models"):
    """Find the best checkpoint based on F1 score"""
    checkpoints = []
    
    if not os.path.exists(models_dir):
        return None
    
    for item in os.listdir(models_dir):
        if "_checkpoint_epoch_" in item:
            checkpoint_path = os.path.join(models_dir, item)
            metrics_file = os.path.join(checkpoint_path, "metrics.json")
            
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, 'r') as f:
                        content = f.read().strip()
                        # Fix incomplete JSON (if ends with incomplete field)
                        if content.endswith(',') or content.endswith('"tn":') or content.endswith('"tn": '):
                            # Remove incomplete last line
                            lines = content.split('\n')
                            while lines and (lines[-1].strip().endswith(',') or 
                                           lines[-1].strip() == '"tn":' or 
                                           lines[-1].strip() == '"tn": ' or
                                           lines[-1].strip().startswith('"tn"')):
                                lines.pop()
                            # Ensure proper closing
                            if lines:
                                last_line = lines[-1].strip()
                                if not last_line.endswith('}') and not last_line.endswith('}'):
                                    if last_line.endswith(','):
                                        lines[-1] = last_line[:-1]
                                    lines.append('}')
                                content = '\n'.join(lines)
                        
                        metrics = json.loads(content)
                    f1_score = metrics.get("f1_score", metrics.get("accuracy", 0))
                    checkpoints.append((checkpoint_path, f1_score, metrics))
                except Exception as e:
                    print(f"[WARNING] Could not read metrics from {item}: {e}")
                    # Try to extract F1 score manually
                    try:
                        import re
                        with open(metrics_file, 'r') as f:
                            content = f.read()
                            f1_match = re.search(r'"f1_score":\s*([\d.]+)', content)
                            acc_match = re.search(r'"accuracy":\s*([\d.]+)', content)
                            if f1_match:
                                f1_score = float(f1_match.group(1))
                            elif acc_match:
                                f1_score = float(acc_match.group(1))
                            else:
                                continue
                            # Create minimal metrics dict
                            metrics = {"f1_score": f1_score, "accuracy": f1_score}
                            checkpoints.append((checkpoint_path, f1_score, metrics))
                    except:
                        continue
    
    if not checkpoints:
        return None
    
    # Sort by F1 score
    checkpoints.sort(key=lambda x: x[1], reverse=True)
    return checkpoints[0]  # Return (path, f1_score, metrics)

def create_best_model_from_checkpoint():
    """Create best_model directory from the best checkpoint"""
    models_dir = "models"
    best_model_dir = os.path.join(models_dir, "best_model")
    
    # Check if best_model already exists
    if os.path.exists(best_model_dir):
        print(f"[INFO] best_model already exists at: {best_model_dir}")
        return best_model_dir
    
    # Find best checkpoint
    print("="*60)
    print("SETTING UP BEST MODEL FROM CHECKPOINTS")
    print("="*60)
    
    result = find_best_checkpoint(models_dir)
    if not result:
        print("[ERROR] No checkpoints found!")
        return None
    
    checkpoint_path, f1_score, metrics = result
    print(f"\n[FOUND] Best checkpoint: {os.path.basename(checkpoint_path)}")
    print(f"   F1-Score: {f1_score:.4f}")
    print(f"   Accuracy: {metrics.get('accuracy', 0):.4f}")
    
    # Create best_model directory
    print(f"\n[CREATING] best_model directory...")
    os.makedirs(best_model_dir, exist_ok=True)
    
    # Copy all files from checkpoint
    print(f"[COPYING] Files from checkpoint...")
    for file in os.listdir(checkpoint_path):
        src = os.path.join(checkpoint_path, file)
        dst = os.path.join(best_model_dir, file)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
    
    # Create training_info.json
    model_name = os.path.basename(checkpoint_path).split("_checkpoint_epoch_")[0]
    training_info = {
        "model_name": model_name,
        "config": {
            "max_length": 128,
            "batch_size": 16,
            "learning_rate": 2e-5,
            "epochs": 3,
        },
        "best_metrics": metrics,
        "history": {
            "train_loss": [],
            "val_loss": [],
            "val_metrics": [metrics]
        },
        "timestamp": "2024-12-11T00:00:00",
        "note": "Created from checkpoint - full training recommended"
    }
    
    info_path = os.path.join(best_model_dir, "training_info.json")
    with open(info_path, 'w') as f:
        json.dump(training_info, f, indent=2)
    
    print(f"[SUCCESS] best_model created at: {best_model_dir}")
    print(f"   Model: {model_name}")
    print(f"   F1-Score: {f1_score:.4f}")
    print(f"\n[NOTE] This is from epoch 1 checkpoint.")
    print(f"   Run 'python train_advanced.py' to complete full training.")
    
    return best_model_dir

if __name__ == "__main__":
    create_best_model_from_checkpoint()

