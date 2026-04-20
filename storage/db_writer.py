"""Database writer for persistence."""

import os
import time
import logging
from typing import Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseWriter:
    """Writer for storing data in PostgreSQL."""

    def __init__(self):
        """Initialize database connection."""
        self.conn = None
        self.cursor = None
        self._connect_with_retry()

    def _connect_with_retry(self):
        """Attempt to connect to PostgreSQL with retry logic."""
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = int(os.getenv('DB_PORT', 5432))
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'password')
        db_name = os.getenv('DB_NAME', 'autorespond')
        timeout = int(os.getenv('DB_TIMEOUT_SECONDS', 30))
        max_attempts = int(os.getenv('DB_CONNECT_RETRIES', 5))
        delay_seconds = int(os.getenv('DB_CONNECT_DELAY_SECONDS', 3))

        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Connecting to PostgreSQL at {db_host}:{db_port} (attempt {attempt}/{max_attempts})")
                self.conn = psycopg2.connect(
                    host=db_host,
                    port=db_port,
                    user=db_user,
                    password=db_password,
                    database=db_name,
                    connect_timeout=timeout
                )
                self.cursor = self.conn.cursor()
                logger.info("Connected to PostgreSQL successfully")
                return
            except psycopg2.OperationalError as e:
                last_error = e
                logger.warning(f"PostgreSQL not ready yet: {e}")
                if attempt < max_attempts:
                    time.sleep(delay_seconds)
            except psycopg2.Error as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise

        logger.error(
            "Unable to connect to PostgreSQL after "
            f"{max_attempts} attempts. Make sure Docker/Postgres is running on "
            f"{db_host}:{db_port} and the database is initialized."
        )
        raise last_error

    def insert_processed_tweet(
        self,
        original_tweet: str,
        cleaned_tweet: str,
        hashed_user_id: str,
        predicted_label: str,
        confidence: float,
        is_duplicate: bool = False,
        is_near_duplicate: bool = False,
        reply_text: Optional[str] = None
    ) -> int:
        """Insert processed tweet into database.
        
        Args:
            original_tweet: Original tweet text
            cleaned_tweet: Cleaned tweet text
            hashed_user_id: SHA256 hashed user ID
            predicted_label: Predicted classification (urgent, informational, complaint)
            confidence: Model confidence score
            is_duplicate: Whether exact duplicate
            is_near_duplicate: Whether near-duplicate
            reply_text: Generated reply text
            
        Returns:
            Tweet ID
        """
        try:
            query = sql.SQL("""
                INSERT INTO processed_tweets 
                (original_tweet, cleaned_tweet, hashed_user_id, predicted_label, 
                 confidence, is_duplicate, is_near_duplicate, reply_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """)
            self.cursor.execute(query, (
                original_tweet, cleaned_tweet, hashed_user_id, predicted_label,
                confidence, is_duplicate, is_near_duplicate, reply_text
            ))
            self.conn.commit()
            tweet_id = self.cursor.fetchone()[0]
            logger.debug(f"Inserted processed tweet {tweet_id}")
            return tweet_id
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error inserting processed tweet: {e}")
            raise

    def insert_reply(self, processed_tweet_id: int, reply_text: str, status: str = 'pending') -> int:
        """Insert reply into outbox.
        
        Args:
            processed_tweet_id: Reference to processed tweet
            reply_text: Reply message
            status: Reply status (pending, sent, failed)
            
        Returns:
            Reply ID
        """
        try:
            query = sql.SQL("""
                INSERT INTO reply_outbox (processed_tweet_id, reply_text, reply_status)
                VALUES (%s, %s, %s)
                RETURNING id
            """)
            self.cursor.execute(query, (processed_tweet_id, reply_text, status))
            self.conn.commit()
            reply_id = self.cursor.fetchone()[0]
            logger.debug(f"Inserted reply {reply_id}")
            return reply_id
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error inserting reply: {e}")
            raise

    def insert_metric(self, metric_name: str, metric_value: float, batch_id: Optional[str] = None):
        """Insert metric into database.
        
        Args:
            metric_name: Name of metric (e.g., 'duplicates_detected', 'accuracy')
            metric_value: Metric value
            batch_id: Batch identifier for grouping
        """
        try:
            query = sql.SQL("""
                INSERT INTO metrics (metric_name, metric_value, batch_id)
                VALUES (%s, %s, %s)
            """)
            self.cursor.execute(query, (metric_name, metric_value, batch_id))
            self.conn.commit()
            logger.debug(f"Inserted metric {metric_name}={metric_value}")
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error inserting metric: {e}")
            raise

    def close(self):
        """Close database connection."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("Database connection closed")
        except psycopg2.Error as e:
            logger.error(f"Error closing database connection: {e}")
