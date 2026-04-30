#!/bin/bash
# Restore the original dataset for the producer
set -e

DATA_DIR="data/sample"
ORIG="$DATA_DIR/tweets_sample.csv"
BACKUP="$DATA_DIR/tweets_sample_original_backup.csv"

if [ ! -f "$BACKUP" ]; then
  echo "No backup found at $BACKUP. Cannot restore."
  exit 1
fi

cp "$BACKUP" "$ORIG"
echo "Restored $ORIG from $BACKUP."
