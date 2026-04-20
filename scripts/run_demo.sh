#!/bin/bash
# AutoRespondX Demo - Step-by-Step Instructions
# This script prints the exact commands to run the demo in separate terminals
# Run from repo root: bash scripts/run_demo.sh

set -e

echo "============================================================"
echo "AutoRespondX - LOCAL MVP DEMO"
echo "============================================================"
echo ""
echo "This demo shows end-to-end streaming data processing with"
echo "ML classification, duplicate detection, and reply generation."
echo ""
echo "The demo requires 4 terminal windows:"
echo "  Terminal 1: PostgreSQL (Docker)"
echo "  Terminal 2: Spark Streaming Job"
echo "  Terminal 3: Kafka Producer (CSV streaming)"
echo "  Terminal 4: Query Results"
echo ""
echo "============================================================"
echo ""

# Check if venv is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠ Virtual environment not activated!"
    echo "Run: source .venv/bin/activate"
    echo ""
fi

# Check if Docker services are running
echo "[CHECK] Verifying Docker services..."
echo ""
if ! docker-compose ps | grep -q "autorespond-postgres"; then
    echo "✗ PostgreSQL not running!"
    echo ""
    echo "Run this first:"
    echo "  docker-compose up -d"
    echo ""
    exit 1
fi

if ! docker-compose ps | grep -q "autorespond-kafka"; then
    echo "✗ Kafka not running!"
    echo ""
    echo "Run this first:"
    echo "  docker-compose up -d"
    echo ""
    exit 1
fi

echo "✓ All Docker services running"
echo ""

echo "============================================================"
echo "DEMO SCRIPT - COPY & PASTE THESE COMMANDS"
echo "============================================================"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Initialize PostgreSQL Schema (Terminal 1)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "bash scripts/init_db.sh"
echo ""
echo "Expected: Tables created (processed_tweets, reply_outbox, metrics)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Train the ML model (Terminal 1 or 2 - runs once)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "source .venv/bin/activate"
echo "python3 -m model.train_model"
echo ""
echo "Expected: Model training results with accuracy scores"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Start Spark Streaming Job (Terminal 2 - LEAVE RUNNING)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "source .venv/bin/activate"
echo "python3 -m streaming.spark_stream"
echo ""
echo "Note: This job runs until interrupted (Ctrl+C)"
echo "      Keep this terminal open while running producer"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Run Kafka Producer (Terminal 3)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "source .venv/bin/activate"
echo "python3 -m producer.kafka_producer"
echo ""
echo "Expected: Messages like 'Sent message 1: user_001 - user_001 message...'"
echo "          30 messages total from sample CSV"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5: Query Results (Terminal 4 - after producer completes)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "# Check processed tweets"
echo "docker-compose exec postgres psql -U postgres -d autorespond -c \\"
echo "  \"SELECT hashed_user_id, predicted_label, confidence, is_duplicate FROM processed_tweets LIMIT 5;\""
echo ""
echo "# Check generated replies"
echo "docker-compose exec postgres psql -U postgres -d autorespond -c \\"
echo "  \"SELECT * FROM reply_outbox LIMIT 5;\""
echo ""
echo "# Check system metrics"
echo "docker-compose exec postgres psql -U postgres -d autorespond -c \\"
echo "  \"SELECT metric_name, AVG(metric_value) as avg_value FROM metrics GROUP BY metric_name;\""
echo ""

echo "============================================================"
echo "CLEANUP (When demo is complete)"
echo "============================================================"
echo ""
echo "# Stop Spark streaming (press Ctrl+C in Terminal 2)"
echo ""
echo "# Stop Docker services"
echo "docker-compose down"
echo ""
echo "# Clean up checkpoint files"
echo "rm -rf /tmp/spark-checkpoint"
echo ""

echo "============================================================"
echo "✓ Demo script ready. Follow the steps above in order."
echo "============================================================"
echo ""

echo "Demo complete!"
