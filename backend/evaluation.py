"""
Advanced evaluation metrics and model comparison utilities.
"""
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from typing import Dict, List, Tuple, Optional
import json
import os
from datetime import datetime


class ModelEvaluator:
    """Comprehensive model evaluation with multiple metrics"""
    
    def __init__(self, save_dir: str = "logs"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, 
                        y_proba: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Calculate comprehensive evaluation metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Predicted probabilities (for ROC-AUC)
            
        Returns:
            Dictionary of metric names and values
        """
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, average="weighted", zero_division=0),
            "recall": recall_score(y_true, y_pred, average="weighted", zero_division=0),
            "f1_score": f1_score(y_true, y_pred, average="weighted", zero_division=0),
            "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
            "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
            "f1_score_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
        }
        
        # Add ROC-AUC if probabilities are provided
        if y_proba is not None and len(np.unique(y_true)) > 1:
            try:
                metrics["roc_auc"] = roc_auc_score(y_true, y_proba[:, 1])
            except:
                metrics["roc_auc"] = 0.0
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        # Convert numpy int64 to Python int for JSON serialization
        metrics["tn"] = int(tn)
        metrics["fp"] = int(fp)
        metrics["fn"] = int(fn)
        metrics["tp"] = int(tp)
        
        # Convert all numpy types to Python types for JSON serialization
        return {k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
                for k, v in metrics.items()}
    
    def evaluate_model(self, model, dataloader, device, tokenizer, 
                      return_predictions: bool = False) -> Tuple[Dict[str, float], Optional[Tuple]]:
        """
        Evaluate a model on a dataloader.
        
        Returns:
            metrics: Dictionary of evaluation metrics
            (predictions, labels, probabilities): If return_predictions=True
        """
        model.eval()
        all_preds = []
        all_labels = []
        all_probs = []
        
        with torch.no_grad():
            for batch in dataloader:
                labels = batch["labels"].cpu().numpy()
                batch_inputs = {k: v.to(device) for k, v in batch.items() if k != "labels"}
                
                outputs = model(**batch_inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1).cpu().numpy()
                preds = np.argmax(probs, axis=-1)
                
                all_preds.extend(preds)
                all_labels.extend(labels)
                all_probs.extend(probs)
        
        all_preds = np.array(all_preds)
        all_labels = np.array(all_labels)
        all_probs = np.array(all_probs)
        
        metrics = self.calculate_metrics(all_labels, all_preds, all_probs)
        
        if return_predictions:
            return metrics, (all_preds, all_labels, all_probs)
        return metrics, None
    
    def print_evaluation_report(self, metrics: Dict[str, float], 
                                model_name: str = "Model",
                                detailed: bool = True):
        """Print formatted evaluation report"""
        print(f"\n{'='*60}")
        print(f"Evaluation Report: {model_name}")
        print(f"{'='*60}")
        
        print(f"\n[MAIN METRICS]")
        print(f"  Accuracy:    {metrics['accuracy']:.4f}")
        print(f"  F1-Score:    {metrics['f1_score']:.4f}")
        print(f"  Precision:   {metrics['precision']:.4f}")
        print(f"  Recall:      {metrics['recall']:.4f}")
        
        if 'roc_auc' in metrics:
            print(f"  ROC-AUC:     {metrics['roc_auc']:.4f}")
        
        if detailed:
            print(f"\n[MACRO-AVERAGED METRICS]")
            print(f"  Precision (Macro): {metrics['precision_macro']:.4f}")
            print(f"  Recall (Macro):    {metrics['recall_macro']:.4f}")
            print(f"  F1-Score (Macro):  {metrics['f1_score_macro']:.4f}")
            
            print(f"\n[CONFUSION MATRIX]")
            print(f"  True Negatives:  {metrics['tn']}")
            print(f"  False Positives: {metrics['fp']}")
            print(f"  False Negatives: {metrics['fn']}")
            print(f"  True Positives:  {metrics['tp']}")
        
        print(f"{'='*60}\n")
    
    def save_evaluation_results(self, metrics: Dict[str, float], 
                                model_name: str,
                                config: Dict = None):
        """Save evaluation results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.save_dir}/evaluation_{model_name}_{timestamp}.json"
        
        # Convert numpy types to Python types for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        results = {
            "model_name": model_name,
            "timestamp": timestamp,
            "metrics": convert_to_serializable(metrics),
            "config": convert_to_serializable(config or {})
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"[SUCCESS] Evaluation results saved to: {filename}")
        return filename


class ModelComparator:
    """Compare multiple models and select the best one"""
    
    def __init__(self, evaluator: ModelEvaluator):
        self.evaluator = evaluator
        self.results = []
    
    def add_model_result(self, model_name: str, metrics: Dict[str, float], 
                        config: Dict = None):
        """Add a model's evaluation results"""
        self.results.append({
            "model_name": model_name,
            "metrics": metrics,
            "config": config or {}
        })
    
    def get_best_model(self, metric: str = "f1_score") -> Dict:
        """Get the best model based on a specific metric"""
        if not self.results:
            raise ValueError("No model results to compare!")
        
        best_result = max(self.results, key=lambda x: x["metrics"].get(metric, 0))
        return best_result
    
    def print_comparison(self, primary_metric: str = "f1_score"):
        """Print comparison table of all models"""
        if not self.results:
            print("No results to compare!")
            return
        
        print(f"\n{'='*80}")
        print(f"MODEL COMPARISON (sorted by {primary_metric})")
        print(f"{'='*80}")
        
        # Sort by primary metric
        sorted_results = sorted(
            self.results, 
            key=lambda x: x["metrics"].get(primary_metric, 0),
            reverse=True
        )
        
        print(f"\n{'Model Name':<25} {'Accuracy':<12} {'F1-Score':<12} "
              f"{'Precision':<12} {'Recall':<12} {'ROC-AUC':<12}")
        print("-" * 80)
        
        for result in sorted_results:
            m = result["metrics"]
            print(f"{result['model_name']:<25} "
                  f"{m.get('accuracy', 0):<12.4f} "
                  f"{m.get('f1_score', 0):<12.4f} "
                  f"{m.get('precision', 0):<12.4f} "
                  f"{m.get('recall', 0):<12.4f} "
                  f"{m.get('roc_auc', 0):<12.4f}")
        
        print(f"{'='*80}\n")
        
        # Show best model
        best = self.get_best_model(primary_metric)
        print(f"[BEST MODEL] {best['model_name']}")
        print(f"   Best {primary_metric}: {best['metrics'].get(primary_metric, 0):.4f}")
    
    def save_comparison(self, filename: str = None):
        """Save comparison results to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.evaluator.save_dir}/model_comparison_{timestamp}.json"
        
        # Convert numpy types to Python types for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        serializable_results = convert_to_serializable(self.results)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"[SUCCESS] Comparison results saved to: {filename}")
        return filename








