# AutoRespondX Synthetic Stress Test Guide

**WARNING:** The 100k synthetic dataset is for stress testing only. It is not a real or collected dataset. Use with caution—processing 100k rows may slow down a single laptop.

## Recommended Order
1. Test with 1k dataset first
2. Then try 5k
3. Only then try 100k (if your machine has enough resources)

---

## Step 1: Generate Synthetic Datasets

```
python3 scripts/generate_synthetic_dataset.py
```

This will create:
- data/sample/tweets_sample_1k.csv
- data/sample/tweets_sample_5k.csv
- data/sample/tweets_sample_100k.csv

---

## Step 2: Switch to a Synthetic Dataset

**Switch to 1k:**
```
bash scripts/use_dataset.sh 1k
```

**Switch to 5k:**
```
bash scripts/use_dataset.sh 5k
```

**Switch to 100k:**
```
bash scripts/use_dataset.sh 100k
```

**Restore the original dataset:**
```
bash scripts/restore_original_dataset.sh
```

---

## Step 3: Run the Full Pipeline

1. **Start Docker services:**
   ```
   docker-compose up -d
   ```
2. **Start Spark streaming:**
   ```
   python3 scripts/run_streaming.py
   ```
3. **Run the Kafka producer:**
   ```
   python3 scripts/run_producer.py
   ```
4. **Verify PostgreSQL row counts:**
   ```
   docker compose exec -T postgres psql -U postgres -d autorespond -c "SELECT COUNT(*) FROM processed_tweets;"
   ```

---

## Notes
- The original dataset is always backed up as `data/sample/tweets_sample_original_backup.csv` the first time you swap.
- You can restore the original at any time with the restore script.
- The synthetic datasets are safe to use and will not overwrite your original data.
- The pipeline logic, producer, Spark, and database schema are NOT changed by this process.
