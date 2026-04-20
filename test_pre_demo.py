#!/usr/bin/env python3
"""Pre-demo integration test."""

import sys
import os

print("=" * 60)
print("PRE-DEMO INTEGRATION TEST")
print("=" * 60)

print("\n[1/4] Testing producer...")
try:
    from producer.kafka_producer import EventProducer
    producer = EventProducer()
    print(f"  ✓ Producer OK (broker: {producer.broker})")
except Exception as e:
    print(f"  ✗ Producer failed: {e}")
    sys.exit(1)

print("\n[2/4] Testing model trainer...")
try:
    from model.train_model import ModelTrainer
    trainer = ModelTrainer()
    assert os.path.exists(trainer.data_path), f"CSV not found"
    print(f"  ✓ Trainer OK (data: {trainer.data_path})")
except Exception as e:
    print(f"  ✗ Trainer failed: {e}")
    sys.exit(1)

print("\n[3/4] Testing model predictor...")
try:
    from model.predict import Predictor
    print(f"  ✓ Predictor class loads OK")
except Exception as e:
    print(f"  ✗ Predictor failed: {e}")
    sys.exit(1)

print("\n[4/4] Testing dedup modules...")
try:
    from dedup.bloom_filter import BloomFilter
    from dedup.lsh_utils import LSHBand
    bf = BloomFilter()
    lsh = LSHBand()
    print(f"  ✓ Bloom Filter and LSH OK")
except Exception as e:
    print(f"  ✗ Dedup failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL PRE-DEMO CHECKS PASSED")
print("=" * 60)
