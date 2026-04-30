#!/bin/bash
# Usage: bash scripts/use_dataset.sh [1k|5k|100k]
# Safely swap the active dataset for the producer
set -e

DATA_DIR="data/sample"
ORIG="$DATA_DIR/tweets_sample.csv"
BACKUP="$DATA_DIR/tweets_sample_original_backup.csv"

if [ $# -ne 1 ]; then
  echo "Usage: bash scripts/use_dataset.sh [1k|5k|100k]"
  exit 1
fi

case "$1" in
  1k)
    NEWFILE="$DATA_DIR/tweets_sample_1k.csv"
    ;;
  5k)
    NEWFILE="$DATA_DIR/tweets_sample_5k.csv"
    ;;
  100k)
    NEWFILE="$DATA_DIR/tweets_sample_100k.csv"
    ;;
  *)
    echo "Invalid argument: $1. Use 1k, 5k, or 100k."
    exit 1
    ;;
esac

if [ ! -f "$NEWFILE" ]; then
  echo "Synthetic dataset $NEWFILE does not exist. Run the generator first."
  exit 1
fi

# Backup original if not already backed up
if [ ! -f "$BACKUP" ]; then
  cp "$ORIG" "$BACKUP"
  echo "Backed up original dataset to $BACKUP."
fi

cp "$NEWFILE" "$ORIG"
echo "Active dataset is now: $ORIG (copied from $NEWFILE)"
