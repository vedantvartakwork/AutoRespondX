"""Model prediction module."""

import os
import pickle
import logging
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class Predictor:
    """Predictor for inference on raw tweet text."""

    def __init__(self):
        """Initialize predictor with saved model and vectorizer."""
        self.model_path = os.getenv('MODEL_PATH', './model/trained_model.pkl')
        self.vectorizer_path = './model/vectorizer.pkl'
        self.model = None
        self.vectorizer = None
        self.label_decoder = {0: 'complaint', 1: 'praise', 2: 'inquiry'}
        self.load_artifacts()

    def load_artifacts(self):
        """Load model and vectorizer from disk."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            logger.info("Model and vectorizer loaded successfully")
        except FileNotFoundError as e:
            logger.error(f"Model artifacts not found: {e}")
            raise

    def predict(self, text: str) -> Tuple[str, float]:
        """Predict label and confidence for raw tweet text.
        
        Args:
            text: Raw tweet text
            
        Returns:
            Tuple of (predicted_label, confidence)
        """
        # Vectorize text
        X = self.vectorizer.transform([text])
        
        # Get prediction
        label_id = self.model.predict(X)[0]
        label = self.label_decoder[label_id]
        
        # Get confidence (max probability)
        proba = self.model.predict_proba(X)[0]
        confidence = max(proba)
        
        return label, confidence

    def predict_batch(self, texts: list) -> list:
        """Predict labels for multiple texts.
        
        Args:
            texts: List of tweet texts
            
        Returns:
            List of (label, confidence) tuples
        """
        results = []
        for text in texts:
            label, confidence = self.predict(text)
            results.append((label, confidence))
        return results
