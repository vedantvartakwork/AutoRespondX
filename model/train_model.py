"""Model training pipeline."""

import os
import pickle
import logging
from typing import Tuple
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier

load_dotenv()
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Trainer for Decision Tree classification model."""

    def __init__(self, data_path: str = None):
        """Initialize model trainer.
        
        Args:
            data_path: Path to training CSV file
        """
        self.data_path = data_path or './data/sample/tweets_sample.csv'
        self.model = DecisionTreeClassifier(max_depth=10, random_state=42)
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.model_path = os.getenv('MODEL_PATH', './model/trained_model.pkl')
        self.vectorizer_path = './model/vectorizer.pkl'
        self.label_encoder = {'complaint': 0, 'praise': 1, 'inquiry': 2}
        self.label_decoder = {v: k for k, v in self.label_encoder.items()}

    def train(self) -> Tuple[float, float]:
        """Train the model from CSV data.
        
        Returns:
            Tuple of (train_accuracy, test_accuracy)
        """
        # Load data
        df = pd.read_csv(self.data_path)
        logger.info(f"Loaded {len(df)} tweets from {self.data_path}")
        
        # Extract features and labels
        X = self.vectorizer.fit_transform(df['message'])
        y = df['label'].map(self.label_encoder).values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        # Report
        y_pred = self.model.predict(X_test)
        logger.info(f"Train Accuracy: {train_score:.3f}")
        logger.info(f"Test Accuracy: {test_score:.3f}")
        logger.info(f"\n{classification_report(y_test, y_pred, target_names=list(self.label_decoder.values()))}")
        
        print(f"\n=== MODEL TRAINING RESULTS ===")
        print(f"Train Accuracy: {train_score:.3f}")
        print(f"Test Accuracy: {test_score:.3f}")
        print(f"============================\n")
        
        return train_score, test_score

    def save_model(self):
        """Save trained model and vectorizer to disk."""
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        logger.info(f"Model saved to {self.model_path}")
        logger.info(f"Vectorizer saved to {self.vectorizer_path}")

    def load_model(self):
        """Load model and vectorizer from disk."""
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)
        with open(self.vectorizer_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
        logger.info("Model and vectorizer loaded")


def main():
    trainer = ModelTrainer()
    trainer.train()
    trainer.save_model()


if __name__ == '__main__':
    main()
