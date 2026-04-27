"""
AutoRespondX Differential Privacy-style Noisy Aggregate Reporting
Privacy-preserving analytics demonstration script (classroom-friendly).
"""
import os
import sys
import math
import random
import psycopg2
from dotenv import load_dotenv

def laplace_noise(scale: float) -> float:
    """Sample Laplace noise using inverse transform sampling (no extra dependencies)."""
    u = random.uniform(-0.5, 0.5)
    return -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))

def add_noise(count: int, epsilon: float) -> int:
    """Add Laplace noise to a count and clamp result to zero or above."""
    scale = 1.0 / epsilon
    noisy = count + laplace_noise(scale)
    return max(0, int(round(noisy)))

def fetch_label_summary(cur):
    cur.execute("SELECT predicted_label, total_count FROM vw_label_summary;")
    return cur.fetchall()

def fetch_duplicate_summary(cur):
    cur.execute("SELECT exact_duplicates, near_duplicates, total_rows FROM vw_duplicate_summary;")
    return cur.fetchone()

def fetch_complaint_spike(cur):
    cur.execute("SELECT complaint_count_last_20 FROM vw_complaint_spike;")
    row = cur.fetchone()
    return row[0] if row else 0

def main():
    load_dotenv()
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_name = os.getenv('DB_NAME', 'autorespond')
    epsilon = float(os.getenv('DP_EPSILON', 1.0))
    seed = int(os.getenv('DP_RANDOM_SEED', 42))
    random.seed(seed)

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            dbname=db_name
        )
    except Exception as e:
        print(f"Could not connect to PostgreSQL: {e}")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            # Label summary
            label_rows = fetch_label_summary(cur)
            # Duplicate summary
            exact, near, total = fetch_duplicate_summary(cur)
            # Complaint spike
            complaint_spike = fetch_complaint_spike(cur)
    except Exception as e:
        print(f"Error querying analytics views: {e}")
        conn.close()
        sys.exit(1)
    conn.close()


    print("\n=== PRIVATE ANALYTICS REPORT ===")
    print(f"Epsilon: {epsilon}\n")

    print("Label Summary (raw → noisy)")
    for label, count in label_rows:
        noisy = add_noise(count, epsilon)
        print(f"{label.capitalize()}: {count} → {noisy}")
    print()

    print("Duplicate Summary (raw → noisy)")
    print(f"Exact duplicates: {exact} → {add_noise(exact, epsilon)}")
    print(f"Near duplicates: {near} → {add_noise(near, epsilon)}")
    print(f"Total rows: {total} → {add_noise(total, epsilon)}\n")

    print("Complaint Spike (raw → noisy)")
    print(f"Complaint count last 20: {complaint_spike} → {add_noise(complaint_spike, epsilon)}\n")

    print("Note: Laplace noise was added to aggregate counts for privacy-preserving analytics demonstration.")
    print("This script demonstrates Differential Privacy-style noisy aggregate reporting for classroom use.")

if __name__ == "__main__":
    main()
