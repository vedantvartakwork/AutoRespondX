"""
AutoRespondX Complaint Spike Alert Script
Read-only, safe, and classroom-demo friendly.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def main():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_name = os.getenv('DB_NAME', 'autorespond')
    threshold = int(os.getenv('COMPLAINT_SPIKE_THRESHOLD', 5))

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            dbname=db_name
        )
    except Exception as e:
        print(f"Error: Could not connect to PostgreSQL: {e}")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT complaint_count_last_20 FROM vw_complaint_spike;")
            row = cur.fetchone()
            if row is None:
                print("No data found in complaint spike view.")
                sys.exit(0)
            count = row[0]
            print(f"Complaint count in the last 20 tweets: {count}")
            if count >= threshold:
                print("ALERT: Complaint spike detected!")
            else:
                print("OK: No complaint spike detected.")
    except Exception as e:
        print(f"Error querying complaint spike view: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
