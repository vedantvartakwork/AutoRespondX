#!/usr/bin/env python3
"""
Generate synthetic customer-support tweet dataset for AutoRespondX stress testing.
- Reads data/sample/tweets_sample.csv
- Preserves schema and column names
- Generates synthetic rows with realistic variations
- Produces 1k, 5k, and 100k row CSVs
- Prints validation info and label frequency summary
- Does NOT overwrite the original dataset
"""
import csv
import random
import os
from datetime import datetime, timedelta
from collections import Counter

INPUT_PATH = 'data/sample/tweets_sample.csv'
OUTPUT_PATHS = {
    1000: 'data/sample/tweets_sample_1k.csv',
    5000: 'data/sample/tweets_sample_5k.csv',
    100000: 'data/sample/tweets_sample_100k.csv',
}
RANDOM_SEED = 22842

# Message templates and variations
COMPLAINTS = [
    "Why is my order taking so long? I ordered it {delay} ago{punct}",
    "My order is taking forever. I ordered it {delay} ago{punct}",
    "Your customer service is absolutely terrible{punct}",
    "I'm very disappointed with this service{punct}",
    "Horrible experience from start to finish{punct}",
    "I am extremely unsatisfied with my purchase{punct}",
    "Incredibly disappointed with the quality{punct}",
    "This is the worst product I have ever purchased{punct}",
]
PRAISES = [
    "Love this product! Best purchase ever{punct}",
    "Just wanted to say thank you for the great experience{punct}",
    "Amazing quality and fast shipping{punct}",
    "Fantastic service! Would definitely recommend{punct}",
    "Absolutely love everything about this company{punct}",
    "This is exactly what I wanted. Five stars{punct}",
    "Your service is outstanding{punct}",
    "Best company ever. Highly recommended{punct}",
]
INQUIRIES = [
    "Can I return an item that was damaged in shipping{punct}",
    "Where can I find the refund policy{punct}",
    "How long does shipping usually take{punct}",
    "Do you offer international shipping{punct}",
    "What is the warranty on this item{punct}",
    "How can I track my shipment{punct}",
    "Can I get a replacement for the defective unit{punct}",
    "Do you have this item in a different size{punct}",
    "How do I contact customer support{punct}",
    "What payment methods do you accept{punct}",
    "Is there a discount code I can use{punct}",
]
DELAYS = ["2 weeks", "10 days", "14 days", "15 days", "a week", "3 weeks"]
PUNCT = [".", "!", "?", ""]

LABEL_TO_TEMPLATES = {
    "complaint": COMPLAINTS,
    "praise": PRAISES,
    "inquiry": INQUIRIES,
}

# Capitalization/wording variations
CAP_VARIANTS = [str.title, str.upper, str.lower, lambda s: s]

# Read input schema and data
with open(INPUT_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    input_rows = list(reader)
    columns = reader.fieldnames

print(f"Detected columns: {columns}")
print(f"Input row count: {len(input_rows)}")

# Helper to generate a synthetic row
def synth_row(idx, label_choices):
    label = random.choice(label_choices)
    template = random.choice(LABEL_TO_TEMPLATES[label])
    delay = random.choice(DELAYS)
    punct = random.choice(PUNCT)
    msg = template.format(delay=delay, punct=punct)
    # Capitalization/wording
    msg = random.choice(CAP_VARIANTS)(msg)
    # Minor word swaps
    if label == "complaint" and random.random() < 0.2:
        msg = msg.replace("order", random.choice(["package", "shipment", "item"]))
    if label == "inquiry" and random.random() < 0.2:
        msg = msg.replace("refund", random.choice(["return", "exchange"]))
    if label == "praise" and random.random() < 0.2:
        msg = msg.replace("great", random.choice(["wonderful", "awesome", "fantastic"]))
    # User ID
    user_id = f"user_{random.randint(100, 99999):05d}"
    # Timestamp: random within 2024, spaced by idx
    base = datetime(2024, 1, 1, 8, 0, 0)
    ts = base + timedelta(minutes=idx * random.randint(1, 5))
    timestamp = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "user_id": user_id,
        "message": msg,
        "timestamp": timestamp,
        "label": label,
    }

# Detect label column and its values
label_col = None
label_values = set()
if 'label' in columns:
    label_col = 'label'
    label_values = set(row['label'] for row in input_rows)
else:
    print("No label column detected. Will randomize labels.")
    label_values = {"complaint", "praise", "inquiry"}
label_choices = list(label_values)

random.seed(RANDOM_SEED)

for n_rows, out_path in OUTPUT_PATHS.items():
    synth_rows = []
    # For 1k and 5k, use more input-based sampling; for 100k, generate more variations
    for i in range(n_rows):
        # Intentionally add some exact/near duplicates
        if i < len(input_rows) and i % 20 == 0:
            row = input_rows[i % len(input_rows)].copy()
            # Small chance to mutate timestamp for realism
            if random.random() < 0.5:
                base = datetime.strptime(row['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                row['timestamp'] = (base + timedelta(minutes=random.randint(1, 60))).strftime("%Y-%m-%dT%H:%M:%SZ")
            synth_rows.append(row)
        else:
            synth_rows.append(synth_row(i, label_choices))
    # Write output
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(synth_rows)
    print(f"Wrote {out_path} with {len(synth_rows)} rows.")
    # Print 5 sample rows
    print(f"Sample rows from {out_path}:")
    for row in synth_rows[:5]:
        print(row)
    # Label frequency summary
    if label_col:
        freq = Counter(row[label_col] for row in synth_rows)
        print(f"Label frequency in {out_path}: {dict(freq)}")
