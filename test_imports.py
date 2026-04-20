#!/usr/bin/env python3
"""Test all imports and basic functionality."""

import sys

try:
    from producer.kafka_producer import EventProducer
    from model.train_model import ModelTrainer
    from model.predict import Predictor
    from dedup.bloom_filter import BloomFilter
    from dedup.lsh_utils import LSHBand
    from storage.db_writer import DatabaseWriter
    from monitoring.metrics import Metrics
    from streaming.spark_stream import StreamProcessor
    
    print("✓ All 8 module imports successful")
    
    # Test basic instantiation
    bf = BloomFilter()
    print("✓ BloomFilter instantiated")
    
    lsh = LSHBand()
    print("✓ LSHBand instantiated")
    
    metrics = Metrics()
    print("✓ Metrics instantiated")
    
    print("\n✓ REPO VALIDATION COMPLETE - ALL SYSTEMS GO")
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
