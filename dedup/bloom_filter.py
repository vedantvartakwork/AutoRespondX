"""Bloom filter for duplicate detection."""

import hashlib
from typing import Any


class BloomFilter:
    """Simple Bloom filter implementation."""

    def __init__(self, size: int = 10000, num_hashes: int = 3):
        """Initialize Bloom filter.
        
        Args:
            size: Size of the bit array
            num_hashes: Number of hash functions
        """
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = [0] * size

    def _hash(self, item: Any, seed: int) -> int:
        """Generate hash value.
        
        Args:
            item: Item to hash
            seed: Seed for hash function
            
        Returns:
            Hash value
        """
        h = hashlib.md5(f"{seed}{item}".encode()).digest()
        return int.from_bytes(h, byteorder='big') % self.size

    def add(self, item: Any):
        """Add item to filter.
        
        Args:
            item: Item to add
        """
        for i in range(self.num_hashes):
            index = self._hash(item, i)
            self.bit_array[index] = 1

    def contains(self, item: Any) -> bool:
        """Check if item might be in filter.
        
        Args:
            item: Item to check
            
        Returns:
            True if item might be in filter, False if definitely not
        """
        for i in range(self.num_hashes):
            index = self._hash(item, i)
            if self.bit_array[index] == 0:
                return False
        return True
