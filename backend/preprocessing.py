"""
Text preprocessing utilities for consistent data cleaning
across training and inference.
"""
from __future__ import annotations

import re
from typing import Optional

try:
    import pandas as pd
except Exception:  # pragma: no cover - runtime path when pandas is unavailable
    pd = None


def clean_text(text: str) -> str:
    """
    Clean and preprocess tweet text:
    - Remove URLs
    - Remove user mentions (@username)
    - Keep hashtags (they can be informative for disaster detection)
    - Remove extra whitespace
    - Handle HTML entities
    
    Args:
        text: Raw tweet text
        
    Returns:
        Cleaned text string
    """
    # Handle None/NaN/non-string values without requiring pandas at runtime.
    if text is None:
        return ""
    if isinstance(text, float) and text != text:
        return ""
    if not isinstance(text, str):
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    
    # Remove user mentions but keep the text
    text = re.sub(r'@\w+', '', text)
    
    # Remove HTML entities
    text = re.sub(r'&[a-zA-Z]+;', '', text)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Comprehensive data preprocessing pipeline:
    - Handle missing values
    - Clean text fields
    - Remove duplicates
    - Filter empty texts
    - Validate target labels
    
    Args:
        df: Raw dataframe with columns: keyword, location, text, target
        
    Returns:
        Preprocessed dataframe
    """
    if pd is None:
        raise ImportError("pandas is required for preprocess_dataframe")

    print("Starting data preprocessing...")
    print(f"Initial dataset shape: {df.shape}")
    
    # Select required columns
    required_cols = ["keyword", "location", "text", "target"]
    df = df[required_cols].copy()
    
    # Check for missing target values
    initial_count = len(df)
    df = df.dropna(subset=["target"])
    print(f"Removed {initial_count - len(df)} rows with missing target")
    
    # Ensure target is integer (0 or 1)
    df["target"] = df["target"].astype(int)
    
    # Validate target values (should be 0 or 1)
    invalid_targets = df[~df["target"].isin([0, 1])]
    if len(invalid_targets) > 0:
        print(f"Warning: Found {len(invalid_targets)} rows with invalid target values. Removing them.")
        df = df[df["target"].isin([0, 1])]
    
    # Clean text column
    print("Cleaning text data...")
    df["text"] = df["text"].apply(clean_text)
    
    # Remove rows with empty text after cleaning
    before_clean = len(df)
    df = df[df["text"].str.len() > 0]
    print(f"Removed {before_clean - len(df)} rows with empty text after cleaning")
    
    # Handle missing keyword and location (fill with empty string)
    df["keyword"] = df["keyword"].fillna("").astype(str)
    df["location"] = df["location"].fillna("").astype(str)
    
    # Clean keyword and location too
    df["keyword"] = df["keyword"].apply(clean_text)
    df["location"] = df["location"].apply(clean_text)
    
    # Remove duplicates
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["text", "target"], keep="first")
    print(f"Removed {before_dedup - len(df)} duplicate rows")
    
    print(f"Final dataset shape: {df.shape}")
    print(f"Class distribution:\n{df['target'].value_counts()}")
    print(f"Class balance: {df['target'].value_counts(normalize=True)}")
    
    return df


def build_full_text(keyword: Optional[str] = None, 
                    location: Optional[str] = None, 
                    text: str = "") -> str:
    """
    Combine keyword + location + text to give model more context.
    Uses special tokens to help the model distinguish between fields.
    
    Args:
        keyword: Optional keyword string
        location: Optional location string
        text: Main tweet text
        
    Returns:
        Combined text with special tokens
    """
    keyword = str(keyword).strip() if keyword else ""
    location = str(location).strip() if location else ""
    text = str(text).strip()
    
    parts = []
    if keyword:
        parts.append(f"[KEYWORD] {keyword}")
    if location:
        parts.append(f"[LOC] {location}")
    parts.append(text)
    
    return " [SEP] ".join(parts)


def prepare_training_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Complete preprocessing pipeline that prepares data for training.
    This includes cleaning, validation, and feature engineering.
    
    Args:
        df: Raw dataframe with columns: keyword, location, text, target
        
    Returns:
        Preprocessed dataframe with 'full_text' column ready for training
    """
    if pd is None:
        raise ImportError("pandas is required for prepare_training_data")

    # Step 1: Clean and validate data
    df = preprocess_dataframe(df)
    
    # Step 2: Build combined text features
    print("\nBuilding combined text features...")
    df["full_text"] = df.apply(
        lambda row: build_full_text(
            keyword=row["keyword"],
            location=row["location"],
            text=row["text"]
        ), axis=1
    )
    
    # Step 3: Print text length statistics
    text_lengths = df["full_text"].str.len()
    print(f"\nText length statistics:")
    print(f"  Mean: {text_lengths.mean():.1f} characters")
    print(f"  Median: {text_lengths.median():.1f} characters")
    print(f"  Max: {text_lengths.max()} characters")
    print(f"  Min: {text_lengths.min()} characters")
    
    return df

