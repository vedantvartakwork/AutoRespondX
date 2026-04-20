# AutoRespondX

**Real-time automated response system** for detecting duplicate inquiries and generating appropriate replies using machine learning.

- **Course**: DATA 228
- **Goal**: Build a runnable local MVP demonstrating end-to-end streaming data processing and ML classification
- **Tech Stack**: PySpark Structured Streaming, Kafka, PostgreSQL, Decision Tree, Bloom Filter, MinHash LSH

---

## Prerequisites

### Required
- Python 3.10+ (`python3 --version`)
- Docker & Docker Compose (`docker --version`, `docker-compose --version`)
- Java JDK 11+ (for Spark)
  - **Mac**: `brew install openjdk@11`
  - **Linux**: `sudo apt-get install openjdk-11-jdk`
  - After install, set: `export JAVA_HOME=$(/usr/libexec/java_home -v 11)`

### Hardware
- 8GB RAM minimum
- 5GB disk space

---

## Quick Start (3 minutes)

### 1. Setup Environment

```bash
# Clone and enter repo
cd /Users/vedantvartak/Desktop/AutoRespondX

# Run setup script
bash scripts/setup.sh
```

This will:
- ✓ Verify Python, Docker, Java
- ✓ Create virtual environment (`.venv/`)
- ✓ Install Python dependencies
- ✓ Start Docker services (Kafka, Zookeeper, PostgreSQL)
- ✓ Initialize PostgreSQL schema

### 2. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 3. View Demo Instructions

```bash
bash scripts/run_demo.sh
```

This prints exact copy-paste commands for running the full demo.

---

## Manual Step-by-Step Demo

### Step 1: Start Docker Services

```bash
docker-compose up -d
sleep 15  # Wait for services to be ready
```

Verify services:
```bash
docker-compose ps
# Should show: autorespond-kafka, autorespond-zookeeper, autorespond-postgres
```

### Step 2: Initialize PostgreSQL Schema

```bash
bash scripts/init_db.sh
```

This script:
- ✓ Checks if PostgreSQL is running
- ✓ Waits for PostgreSQL to be ready (max 30 seconds)
- ✓ Applies `storage/schema.sql`
- ✓ Verifies tables were created

Output should show: `processed_tweets`, `reply_outbox`, `metrics`

### Step 3: Train the ML Model

```bash
source .venv/bin/activate

python3 -m model.train_model
```

Output should show training accuracy scores and save model to `model/trained_model.pkl`.

### Step 4: Start Spark Streaming Job (Terminal 2)

```bash
source .venv/bin/activate

python3 -m streaming.spark_stream
```

> This uses the Spark Kafka connector via `PYSPARK_SUBMIT_ARGS`.

**Keep this terminal open.** This job runs until interrupted (Ctrl+C).

### Step 5: Run Kafka Producer (Terminal 3)

```bash
source .venv/bin/activate

python3 -m producer.kafka_producer
```

This streams 30 CSV rows to Kafka. Output example:
```
Sent message 1: user_001 - Why is my order taking so long?...
Sent message 2: user_002 - Love this product! Best purchase...
...
Finished streaming 30 messages
```

### Step 6: Query Results (Terminal 4)

**After producer completes, query the database:**

#### Processed Tweets
```bash
docker-compose exec postgres psql -U postgres -d autorespond -c "
SELECT 
  id,
  hashed_user_id,
  predicted_label,
  ROUND(confidence::numeric, 3) as confidence,
  is_duplicate,
  is_near_duplicate
FROM processed_tweets
LIMIT 10;
"
```

#### Reply Outbox
```bash
docker-compose exec postgres psql -U postgres -d autorespond -c "
SELECT 
  id,
  processed_tweet_id,
  reply_text,
  reply_status
FROM reply_outbox
LIMIT 10;
"
```

#### System Metrics
```bash
docker-compose exec postgres psql -U postgres -d autorespond -c "
SELECT 
  metric_name,
  COUNT(*) as count,
  ROUND(AVG(metric_value)::numeric, 3) as avg_value
FROM metrics
GROUP BY metric_name;
"
```

---

## Troubleshooting

### Kafka Connection Refused

**Error**: `Connection refused connecting to localhost:9092`

**Fix**:
```bash
# Verify Kafka is running
docker-compose ps | grep kafka

# If not running:
docker-compose up -d kafka

# Wait 10 seconds and retry
sleep 10
```

### PostgreSQL Connection Failed

**Error**: `could not connect to server: Connection refused`

**Fix**:
```bash
# Verify Postgres is running
docker-compose ps | grep postgres

# If not running:
docker-compose up -d postgres

# Initialize schema:
docker-compose exec postgres psql -U postgres -d autorespond -f /docker-entrypoint-initdb.d/01-schema.sql

# Wait 5 seconds and retry
sleep 5
```

### Spark Out of Memory

**Error**: `java.lang.OutOfMemoryError` or `spark.driver.memory`

**Fix**:
```bash
# Increase Docker memory allocation:
# - Docker Desktop > Preferences > Resources > Memory: set to 8GB+

# Or run Spark with explicit memory:
SPARK_DRIVER_MEMORY=2g python3 -m streaming.spark_stream
```

### Java Not Found

**Error**: `JAVA_HOME not set` or `java: command not found`

**Fix**:
```bash
# Install Java
brew install openjdk@11

# Set JAVA_HOME
export JAVA_HOME=$(/usr/libexec/java_home -v 11)

# Add to ~/.zshrc or ~/.bash_profile for persistence:
echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 11)' >> ~/.zshrc
source ~/.zshrc
```

### Model File Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: './model/trained_model.pkl'`

**Fix**:
```bash
# Train the model first (Step 3 above)
python3 -m model.train_model
```

### Port Already in Use

**Error**: `bind: Address already in use` (for 5432, 9092, 2181)

**Fix**:
```bash
# Kill process on port (example: 5432)
lsof -i :5432
kill -9 <PID>

# Or stop all containers
docker-compose down
docker-compose up -d
```

### Checkpoint Directory Error

**Error**: `org.apache.hadoop.security.AccessControlException` in `/tmp/spark-checkpoint`

**Fix**:
```bash
# Clean checkpoint directory
rm -rf /tmp/spark-checkpoint

# Restart Spark streaming job
```

---

## Architecture

```
CSV → Kafka Producer → Kafka Topic → Spark Stream →
  ├─ Bloom Filter (exact dedup)
  ├─ LSH (near-duplicate detection)
  └─ Decision Tree (classification)
    ├─ DB Writer (hash username, store)
    └─ Reply Generator (high-conf direct, low-conf fallback)
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Producer** | `producer/kafka_producer.py` | CSV → Kafka streaming |
| **Streaming** | `streaming/spark_stream.py` | Kafka → Spark processing |
| **Model Trainer** | `model/train_model.py` | Decision Tree classifier |
| **Model Predictor** | `model/predict.py` | Inference on raw text |
| **Dedup** | `dedup/bloom_filter.py` | Exact duplicate detection |
| **LSH** | `dedup/lsh_utils.py` | Near-duplicate detection |
| **Storage** | `storage/db_writer.py` | PostgreSQL persistence |
| **Metrics** | `monitoring/metrics.py` | Prometheus metrics |

---

## Environment Variables

All configured in `.env` (copy from `.env.example`):

```env
# Kafka
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC=raw_tweets
CSV_PATH=./data/sample/tweets_sample.csv
MESSAGE_DELAY_SECONDS=1.0

# Spark
SPARK_MASTER=local[*]
SPARK_APP_NAME=AutoRespondStreaming
SPARK_CHECKPOINT_DIR=/tmp/spark-checkpoint

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=autorespond

# Model
MODEL_PATH=./model/trained_model.pkl
MODEL_CONFIDENCE_THRESHOLD=0.8
```

---

## File Structure

```
AutoRespondX/
├── producer/kafka_producer.py        # CSV → Kafka
├── streaming/spark_stream.py         # Kafka → Processing
├── model/
│   ├── train_model.py               # Decision Tree trainer
│   └── predict.py                    # Inference
├── dedup/
│   ├── bloom_filter.py              # Exact dedup
│   └── lsh_utils.py                 # Near-dedup (LSH)
├── storage/
│   ├── schema.sql                    # PostgreSQL schema
│   └── db_writer.py                  # DB persistence
├── monitoring/metrics.py             # Prometheus metrics
├── scripts/
│   ├── setup.sh                      # One-time setup
│   └── run_demo.sh                   # Demo instructions
├── data/sample/tweets_sample.csv    # 30 sample tweets
├── docker-compose.yml                # Kafka, Zookeeper, Postgres
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment template
└── README.md                         # This file
```

---

## Clean Up

After demo:

```bash
# Stop Spark streaming (Ctrl+C in Terminal 2)

# Stop Docker services
docker-compose down

# Remove Spark checkpoint
rm -rf /tmp/spark-checkpoint

# Remove model files (optional)
rm model/trained_model.pkl model/vectorizer.pkl
```

---

## References

- [PySpark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Bloom Filter](https://en.wikipedia.org/wiki/Bloom_filter)
- [MinHash & LSH](https://en.wikipedia.org/wiki/Locality-sensitive_hashing)
- [Kafka Python](https://kafka-python.readthedocs.io/)
- [Decision Tree Classifier](https://scikit-learn.org/stable/modules/tree.html)

---

**Last Updated**: April 2026  
**Status**: ✓ Ready for local demo