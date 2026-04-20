"""Locality Sensitive Hashing utilities for similarity detection."""

import hashlib
from typing import List
import numpy as np


class LSHBand:
    """LSH band for clustering similar items."""

    def __init__(self, num_rows: int = 5):
        """Initialize LSH band.
        
        Args:
            num_rows: Number of rows per band
        """
        self.num_rows = num_rows
        self.buckets = {}

    def hash_vector(self, vector: List[float], band_id: int) -> str:
        """Hash vector to bucket.
        
        Args:
            vector: Input vector
            band_id: Band identifier
            
        Returns:
            Bucket key
        """
        vector_bytes = np.array(vector[:self.num_rows]).tobytes()
        h = hashlib.sha256(vector_bytes).hexdigest()
        return f"band_{band_id}_{h}"

    def add_vector(self, vector: List[float], item_id: str, band_id: int):
        """Add vector to bucket.
        
        Args:
            vector: Input vector
            item_id: Identifier for the item
            band_id: Band identifier
        """
        bucket = self.hash_vector(vector, band_id)
        if bucket not in self.buckets:
            self.buckets[bucket] = []
        self.buckets[bucket].append(item_id)

    def get_candidates(self, vector: List[float], band_id: int) -> List[str]:
        """Get candidate similar items.
        
        Args:
            vector: Input vector
            band_id: Band identifier
            
        Returns:
            List of similar item IDs
        """
        bucket = self.hash_vector(vector, band_id)
        return self.buckets.get(bucket, [])
