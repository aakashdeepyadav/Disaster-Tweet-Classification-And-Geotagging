import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from tqdm import tqdm
from preprocessing import prepare_training_data

MODEL_DIR = "models/disaster_model"
MAX_LEN = 96
BATCH_SIZE = 16
EPOCHS = 3

class TweetDataset(Dataset):
    def __init__(self, full_texts, labels, tokenizer, max_len=MAX_LEN):
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


def main():
    """
    Simple training script for quick model training.
    For advanced features (model comparison, hyperparameter tuning), use train_advanced.py
    """
    # Load dataset
    print("="*60)
    print("SIMPLE MODEL TRAINING")
    print("="*60)
    print("Loading dataset...")
    if not os.path.exists("train.csv"):
        raise FileNotFoundError(
            "train.csv not found! Please download it from Kaggle and place it in the backend/ directory.\n"
            "Get it from: https://www.kaggle.com/c/nlp-getting-started/data"
        )
    
    df = pd.read_csv("train.csv")
    
    # Preprocess data (all preprocessing happens here)
    df = prepare_training_data(df)
    
    # Split into train/validation sets
    print("\nSplitting data into train/validation sets...")
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df["full_text"].tolist(),
        df["target"].tolist(),
        test_size=0.2,
        random_state=42,
        stratify=df["target"],
    )
    
    print(f"Train set: {len(train_texts)} samples")
    print(f"Validation set: {len(val_texts)} samples")
    
    # Initialize model and tokenizer
    print("\nInitializing model and tokenizer...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=2
    )

    train_ds = TweetDataset(train_texts, train_labels, tokenizer)
    val_ds = TweetDataset(val_texts, val_labels, tokenizer)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    optimizer = AdamW(model.parameters(), lr=2e-5)
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=0, num_training_steps=total_steps
    )

    for epoch in range(EPOCHS):
        print(f"\n=== Epoch {epoch+1}/{EPOCHS} ===")
        model.train()
        total_loss = 0

        for batch in tqdm(train_loader, desc="Training"):
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)
        print(f"Train loss: {avg_train_loss:.4f}")

        # Validation
        model.eval()
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                labels = batch["labels"].cpu().numpy()
                batch = {k: v.to(device) for k, v in batch.items()}
                outputs = model(**batch)
                logits = outputs.logits
                preds = torch.argmax(logits, dim=-1).cpu().numpy()
                all_preds.extend(list(preds))
                all_labels.extend(list(labels))

        print("\nValidation report:")
        print(classification_report(all_labels, all_preds, digits=4))

    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    print(f"Model saved to {MODEL_DIR}")

if __name__ == "__main__":
    main()

