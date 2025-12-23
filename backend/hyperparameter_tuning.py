"""
Hyperparameter tuning using grid search or random search.
Finds the best hyperparameters for a given model.
"""
import os
import itertools
import random
from typing import Dict, List, Tuple
import json
from datetime import datetime

from config import ModelConfig, TrainingConfig, HYPERPARAMETER_SEARCH_SPACE, DEFAULT_CONFIG
from train_advanced import train_single_model, load_and_prepare_data, create_data_loaders
from evaluation import ModelEvaluator


class HyperparameterTuner:
    """Hyperparameter tuning with grid search or random search"""
    
    def __init__(self, base_model_config: ModelConfig, training_config: TrainingConfig):
        self.base_config = base_model_config
        self.training_config = training_config
        self.evaluator = ModelEvaluator(save_dir=training_config.log_dir)
        self.results = []
    
    def grid_search(self, search_space: Dict, max_combinations: int = 20) -> Dict:
        """
        Perform grid search over hyperparameter space.
        
        Args:
            search_space: Dictionary of parameter names to lists of values
            max_combinations: Maximum number of combinations to try
            
        Returns:
            Best hyperparameters and their results
        """
        print("\n" + "="*80)
        print("HYPERPARAMETER TUNING - GRID SEARCH")
        print("="*80)
        
        # Generate all combinations
        keys = list(search_space.keys())
        values = list(search_space.values())
        all_combinations = list(itertools.product(*values))
        
        # Limit combinations if too many
        if len(all_combinations) > max_combinations:
            print(f"⚠️  {len(all_combinations)} combinations found, sampling {max_combinations} random combinations")
            all_combinations = random.sample(all_combinations, max_combinations)
        
        print(f"Testing {len(all_combinations)} hyperparameter combinations...")
        
        # Load data once
        df = load_and_prepare_data(self.training_config)
        train_df, val_df, _ = create_data_loaders(df, self.base_config, self.training_config)
        
        best_result = None
        best_metric = -float('inf')
        
        for i, combination in enumerate(all_combinations, 1):
            # Create model config with these hyperparameters
            params = dict(zip(keys, combination))
            model_config = self._create_model_config(params)
            
            print(f"\n{'#'*80}")
            print(f"COMBINATION {i}/{len(all_combinations)}")
            print(f"{'#'*80}")
            print(f"Parameters: {params}")
            
            try:
                # Train model
                results, tokenizer = train_single_model(
                    model_config, train_df, val_df, self.training_config
                )
                
                metrics = results["best_metrics"]
                metric_value = metrics.get(self.training_config.best_model_metric, 0)
                
                # Store result
                result = {
                    "parameters": params,
                    "metrics": metrics,
                    "model_config": {
                        "name": model_config.name,
                        "max_length": model_config.max_length,
                        "batch_size": model_config.batch_size,
                        "learning_rate": model_config.learning_rate,
                        "epochs": model_config.epochs,
                        "weight_decay": model_config.weight_decay,
                        "warmup_steps": model_config.warmup_steps,
                    }
                }
                self.results.append(result)
                
                print(f"✅ {self.training_config.best_model_metric}: {metric_value:.4f}")
                
                # Check if best
                if metric_value > best_metric:
                    best_metric = metric_value
                    best_result = result
                    print(f"🏆 New best combination!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        # Print results
        self._print_results(best_result)
        
        # Save results
        self._save_results()
        
        return best_result
    
    def random_search(self, search_space: Dict, n_iter: int = 10) -> Dict:
        """
        Perform random search over hyperparameter space.
        
        Args:
            search_space: Dictionary of parameter names to lists of values
            n_iter: Number of random combinations to try
            
        Returns:
            Best hyperparameters and their results
        """
        print("\n" + "="*80)
        print("HYPERPARAMETER TUNING - RANDOM SEARCH")
        print("="*80)
        print(f"Testing {n_iter} random hyperparameter combinations...")
        
        # Load data once
        df = load_and_prepare_data(self.training_config)
        train_df, val_df, _ = create_data_loaders(df, self.base_config, self.training_config)
        
        best_result = None
        best_metric = -float('inf')
        
        for i in range(n_iter):
            # Randomly sample hyperparameters
            params = {
                key: random.choice(values) 
                for key, values in search_space.items()
            }
            
            model_config = self._create_model_config(params)
            
            print(f"\n{'#'*80}")
            print(f"ITERATION {i+1}/{n_iter}")
            print(f"{'#'*80}")
            print(f"Parameters: {params}")
            
            try:
                # Train model
                results, tokenizer = train_single_model(
                    model_config, train_df, val_df, self.training_config
                )
                
                metrics = results["best_metrics"]
                metric_value = metrics.get(self.training_config.best_model_metric, 0)
                
                # Store result
                result = {
                    "parameters": params,
                    "metrics": metrics,
                    "model_config": {
                        "name": model_config.name,
                        "max_length": model_config.max_length,
                        "batch_size": model_config.batch_size,
                        "learning_rate": model_config.learning_rate,
                        "epochs": model_config.epochs,
                    }
                }
                self.results.append(result)
                
                print(f"✅ {self.training_config.best_model_metric}: {metric_value:.4f}")
                
                # Check if best
                if metric_value > best_metric:
                    best_metric = metric_value
                    best_result = result
                    print(f"🏆 New best combination!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        # Print results
        self._print_results(best_result)
        
        # Save results
        self._save_results()
        
        return best_result
    
    def _create_model_config(self, params: Dict) -> ModelConfig:
        """Create a ModelConfig from hyperparameters"""
        return ModelConfig(
            name=self.base_config.name,
            model_path=self.base_config.model_path,
            tokenizer_path=self.base_config.tokenizer_path,
            max_length=params.get("max_length", self.base_config.max_length),
            batch_size=params.get("batch_size", self.base_config.batch_size),
            learning_rate=params.get("learning_rate", self.base_config.learning_rate),
            epochs=params.get("epochs", self.base_config.epochs),
            warmup_steps=params.get("warmup_steps", self.base_config.warmup_steps),
            weight_decay=params.get("weight_decay", self.base_config.weight_decay),
        )
    
    def _print_results(self, best_result: Dict):
        """Print tuning results"""
        if not best_result:
            print("No successful results!")
            return
        
        print("\n" + "="*80)
        print("HYPERPARAMETER TUNING RESULTS")
        print("="*80)
        
        print(f"\n🏆 Best Hyperparameters:")
        for key, value in best_result["parameters"].items():
            print(f"  {key}: {value}")
        
        print(f"\n📊 Best Metrics:")
        for key, value in best_result["metrics"].items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value:.4f}")
        
        # Show top 5 results
        sorted_results = sorted(
            self.results,
            key=lambda x: x["metrics"].get(self.training_config.best_model_metric, 0),
            reverse=True
        )
        
        print(f"\n📈 Top 5 Results:")
        for i, result in enumerate(sorted_results[:5], 1):
            metric = result["metrics"].get(self.training_config.best_model_metric, 0)
            print(f"  {i}. {self.training_config.best_model_metric}: {metric:.4f}")
            print(f"     LR: {result['parameters'].get('learning_rate')}, "
                  f"BS: {result['parameters'].get('batch_size')}, "
                  f"ML: {result['parameters'].get('max_length')}")
    
    def _save_results(self):
        """Save tuning results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            self.training_config.log_dir,
            f"hyperparameter_tuning_{timestamp}.json"
        )
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Results saved to: {filename}")


if __name__ == "__main__":
    from config import MODEL_CONFIGS
    
    print("\n" + "="*80)
    print("HYPERPARAMETER TUNING")
    print("="*80)
    
    # Use first model as base
    base_config = MODEL_CONFIGS[0]
    
    # Create tuner
    tuner = HyperparameterTuner(base_config, DEFAULT_CONFIG)
    
    # Run random search (faster than grid search)
    print("\nChoose search method:")
    print("1. Random Search (faster, recommended)")
    print("2. Grid Search (slower, exhaustive)")
    
    choice = input("Enter choice (1 or 2, default=1): ").strip() or "1"
    
    if choice == "2":
        best = tuner.grid_search(HYPERPARAMETER_SEARCH_SPACE, max_combinations=15)
    else:
        n_iter = input("Number of iterations (default=10): ").strip()
        n_iter = int(n_iter) if n_iter else 10
        best = tuner.random_search(HYPERPARAMETER_SEARCH_SPACE, n_iter=n_iter)
    
    if best:
        print(f"\n✅ Best hyperparameters found!")
        print(f"   Best {DEFAULT_CONFIG.best_model_metric}: {best['metrics'].get(DEFAULT_CONFIG.best_model_metric, 0):.4f}")













