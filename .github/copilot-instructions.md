# AutoRespondX - DATA 228 Project

## Project Overview

AutoRespondX is a real-time automated response system that detects duplicate user inquiries and generates appropriate replies using machine learning. The system processes CSV data streamed through Kafka, identifies exact and near-duplicates, and uses a Decision Tree classifier to determine response strategy.

**Course**: DATA 228  
**Goal**: Build a runnable local MVP that demonstrates end-to-end streaming data processing and ML classification.

## Architecture

### Core Components

1. **Producer** (`producer/kafka_producer.py`)
   - Reads CSV data row by row
   - Sends events to Kafka topic `autorespond-events`
   - Each message: `{user_id, message, timestamp}`

2. **Streaming** (`streaming/spark_stream.py`)
   - PySpark Structured Streaming consumer
   - Checkpoint data to `/tmp/spark-checkpoint`
   - Processes one micro-batch every 10 seconds
   - Deduplicates and classifies messages

3. **Deduplication** (`dedup/`)
   - **Exact duplicates**: Bloom Filter (`bloom_filter.py`)
   - **Near duplicates**: Simple MinHash-based LSH (`lsh_utils.py`)
   - Maintains in-memory dedup state for MVP

4. **Model** (`model/`)
   - Decision Tree classifier (`train_model.py`)
   - Predicts: urgent, informational, complaint
   - Inference via `predict.py`
   - Model saved as `model/trained_model.pkl`

5. **Storage** (`storage/`)
   - PostgreSQL with schema in `schema.sql`
   - Tables: `events`, `predictions`, `deduplication_log`
   - Username hashing on write (SHA256)
   - `db_writer.py` for persistence

6. **Monitoring** (`monitoring/metrics.py`)
   - Prometheus metrics: events processed, duplicates detected, accuracy
   - Lightweight logging to stdout

### Data Flow

```
CSV → Kafka Producer → Kafka Topic → Spark Stream → 
  ├─ Bloom Filter (exact dedup)
  ├─ LSH (near-duplicate detection)
  └─ Decision Tree (classification)
    ├─ DB Writer (hash username, store)
    └─ Reply Generator (high-conf direct, low-conf fallback)
```

## Technology Stack

- **Stream Processing**: PySpark Structured Streaming 3.4.1
- **Message Queue**: Kafka (via docker-compose)
- **Database**: PostgreSQL (via docker-compose)
- **ML Model**: scikit-learn Decision Tree
- **Duplicate Detection**: Bloom Filter + MinHash-based LSH
- **Monitoring**: Prometheus client

## Development Guidelines

### Python Standards
- Follow PEP 8 strictly
- Use type hints for all function signatures
- Include docstrings for all public functions and classes
- Keep functions <30 lines, classes focused on single responsibility
- Use descriptive names: `detect_exact_duplicates()` not `dedup()`

### Code Organization
- Minimize dependencies between modules
- Keep demo code in `scripts/` directory
- Use environment variables for all config (see `.env.example`)
- Add error handling and logging at module boundaries

### Testing & Validation
- Minimal unit tests in separate test file if needed
- Focus on end-to-end demo that works locally
- Log all major operations to stdout with timestamps

## Key Implementation Requirements

### 1. Exact Duplicate Detection (Bloom Filter)
```python
from dedup.bloom_filter import BloomFilter

bf = BloomFilter(size=100000, num_hashes=3)
bf.add(user_message)
if bf.contains(user_message):
    # Likely duplicate
    metrics.record_duplicate()
```

### 2. Near-Duplicate Detection (MinHash LSH)
```python
from dedup.lsh_utils import LSHBand

lsh = LSHBand(num_rows=5)
candidates = lsh.get_candidates(message_vector, band_id=0)
# Candidates are similar messages for manual inspection
```

### 3. Decision Tree Classification
```python
from model.train_model import ModelTrainer
from model.predict import Predictor

# Training
trainer = ModelTrainer()
trainer.train(X_features, y_labels)
trainer.save_model()

# Inference
predictor = Predictor()
prediction = predictor.predict(features)  # 'urgent', 'informational', 'complaint'
probabilities = predictor.predict_proba(features)
```

### 4. Username Hashing Before Storage
```python
import hashlib

def hash_username(username: str) -> str:
    return hashlib.sha256(username.encode()).hexdigest()

# Always hash before writing to DB
hashed_user = hash_username(user_id)
db_writer.write_event(hashed_user, message_data)
```

### 5. Checkpointing in Spark
```python
query = df \
    .writeStream \
    .format("parquet") \
    .option("checkpointLocation", "/tmp/spark-checkpoint") \
    .option("path", "/tmp/spark-output") \
    .start()
```

### 6. Reply Generation with Fallback
```python
def generate_reply(prediction: str, confidence: float, fallback_msg: str) -> str:
    if confidence > 0.8:
        return reply_templates[prediction]
    else:
        return fallback_msg  # "Thank you for your message, we'll review it shortly."
```

## Local MVP Setup & Run Commands

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- 8GB RAM (Spark needs memory)

### Setup
```bash
# Clone and enter project
cd /Users/vedantvartak/Desktop/AutoRespondX

# Copy env template
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Start Docker services (Kafka, Zookeeper, PostgreSQL)
docker-compose up -d

# Wait 15 seconds for services to boot
sleep 15

# Initialize database
psql -h localhost -U postgres -d autorespond -f storage/schema.sql
```

### Run MVP Demo (Full End-to-End)
```bash
cd /Users/vedantvartak/Desktop/AutoRespondX

# Terminal 1: Start producer (reads sample CSV, sends to Kafka)
python3 scripts/run_producer.py

# Terminal 2: Start Spark streaming job (processes stream, writes to DB)
python3 scripts/run_streaming.py

# Terminal 3: Train model and run inference
python3 scripts/run_inference.py

# Terminal 4: Monitor output
tail -f /tmp/autorespond.log
```

### Individual Component Tests
```bash
# Test Bloom Filter
python3 -c "from dedup.bloom_filter import BloomFilter; bf = BloomFilter(); bf.add('test'); print(bf.contains('test'))"

# Test LSH
python3 -c "from dedup.lsh_utils import LSHBand; lsh = LSHBand(); lsh.add_vector([1,2,3,4,5], 'item1', 0); print(lsh.get_candidates([1,2,3,4,5], 0))"

# Train model
python3 -c "from model.train_model import ModelTrainer; import numpy as np; t = ModelTrainer(); X = np.random.rand(100, 10); y = np.random.randint(0, 3, 100); print(t.train(X, y))"

# Test producer
python3 producer/kafka_producer.py

# Test streaming
python3 streaming/spark_stream.py
```

### Clean Up
```bash
# Stop and remove Docker containers
docker-compose down

# Clean Spark checkpoint
rm -rf /tmp/spark-checkpoint

# Clean output
rm -f /tmp/spark-output/* /tmp/autorespond.log
```

## File Structure & Responsibilities

```
AutoRespondX/
├── producer/
│   └── kafka_producer.py       # CSV → Kafka (row-by-row streaming)
├── streaming/
│   └── spark_stream.py         # Kafka → Spark (process, dedup, classify)
├── model/
│   ├── train_model.py          # Decision Tree trainer
│   └── predict.py              # Inference with probabilities
├── dedup/
│   ├── bloom_filter.py         # Exact duplicate detection
│   └── lsh_utils.py            # Near-duplicate detection (MinHash)
├── storage/
│   ├── schema.sql              # PostgreSQL schema
│   └── db_writer.py            # Hash username, persist to DB
├── monitoring/
│   └── metrics.py              # Prometheus metrics
├── scripts/
│   ├── run_producer.py         # Launch producer
│   ├── run_streaming.py        # Launch Spark stream
│   └── run_inference.py        # Train model + inference demo
├── data/
│   └── sample/                 # Sample CSV input files
├── docker-compose.yml          # Kafka, Zookeeper, PostgreSQL
├── requirements.txt            # Python dependencies
├── .env.example                # Environment config template
└── README.md                   # Project overview
```

## Configuration (Environment Variables)

See `.env.example` for all options:
```
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC=autorespond-events
SPARK_MASTER=local[4]
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=autorespond
MODEL_PATH=./model/trained_model.pkl
ENVIRONMENT=development
```

## Demo Strategy

**Goal: Show end-to-end processing in <5 minutes**

1. Start producer with 100-row sample CSV (includes duplicates)
2. Show Kafka receiving events
3. Run Spark stream, watch deduplication happen
4. Classify messages with Decision Tree
5. Query database to show hashed usernames and predictions
6. Demonstrate fallback reply when confidence is low

## Key Principles for MVP

✅ **Prioritize**: Runnable local code over optimization  
✅ **Simplify**: Explain architecture in 1-2 minutes  
✅ **Exact**: Generate reproducible run commands  
✅ **Demo**: Test everything end-to-end before submission  
✅ **Document**: Every component has a clear purpose

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Kafka not connecting | `docker-compose ps` - ensure kafka container is running. Wait 20s after `docker-compose up -d` |
| Spark out of memory | Reduce batch size or increase Docker memory (Edit Docker preferences) |
| PostgreSQL connection refused | Ensure `docker-compose up -d` succeeded. Check `psql -h localhost -U postgres -l` |
| Port conflicts (9092, 5432) | Kill processes: `lsof -i :9092` then `kill -9 <PID>` |
| Model file not found | Run `python3 scripts/run_inference.py` first to train and save model |

## References

- [PySpark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Bloom Filter Theory](https://en.wikipedia.org/wiki/Bloom_filter)
- [MinHash & LSH](https://en.wikipedia.org/wiki/Locality-sensitive_hashing)
- [Decision Tree Classifier](https://scikit-learn.org/stable/modules/tree.html)
- [Kafka & Python](https://kafka-python.readthedocs.io/)
