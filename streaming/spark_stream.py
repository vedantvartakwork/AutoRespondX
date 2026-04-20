"""Spark streaming for real-time data processing."""

import os
import json
import hashlib
import logging
from dotenv import load_dotenv

load_dotenv()
if 'PYSPARK_SUBMIT_ARGS' not in os.environ:
    os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 pyspark-shell'

from pyspark.sql import SparkSession
from storage.db_writer import DatabaseWriter
from model.predict import Predictor

logger = logging.getLogger(__name__)


class StreamProcessor:
    """Real-time stream processor using Spark."""

    def __init__(self):
        """Initialize Spark session, model, and database writer."""
        self.spark = SparkSession.builder \
            .appName(os.getenv('SPARK_APP_NAME', 'AutoRespondStreaming')) \
            .master(os.getenv('SPARK_MASTER', 'local[*]')) \
            .getOrCreate()
        self.predictor = Predictor()
        self.db_writer = DatabaseWriter()

    @staticmethod
    def _hash_user_id(user_id: str) -> str:
        """Hash the user identifier before storing."""
        return hashlib.sha256(user_id.encode('utf-8')).hexdigest()


    def _generate_reply(self, label: str, confidence: float, fallback_msg: str = "Thank you for your message. We'll review it shortly.") -> str:
        templates = {
            'complaint': "We're sorry to hear about your experience. Our team will address your concern as soon as possible.",
            'praise': "Thank you for your positive feedback! We're glad you had a great experience.",
            'inquiry': "Thank you for your question. We'll get back to you with more information soon."
        }
        if confidence > 0.8 and label in templates:
            return templates[label]
        return fallback_msg

    def _process_batch(self, batch_df, epoch_id: int):
        """Process each micro-batch from the Kafka stream."""
        if batch_df.rdd.isEmpty():
            logger.info(f"No records in batch {epoch_id}")
            return

        rows = batch_df.selectExpr("CAST(value AS STRING) AS value").collect()
        logger.info(f"Processing batch {epoch_id} with {len(rows)} records")

        processed_count = 0
        duplicate_count = 0
        near_duplicate_count = 0
        low_confidence_count = 0

        for row in rows:
            try:
                event = json.loads(row.value)
                message = event.get('message', '')
                user_id = event.get('user_id', 'unknown')
                label, confidence = self.predictor.predict(message)
                hashed_user = self._hash_user_id(user_id)

                # For MVP, treat all as not duplicate
                is_duplicate = False
                is_near_duplicate = False
                if confidence < 0.8:
                    low_confidence_count += 1

                reply_text = self._generate_reply(label, confidence)

                tweet_id = self.db_writer.insert_processed_tweet(
                    original_tweet=message,
                    cleaned_tweet=message,
                    hashed_user_id=hashed_user,
                    predicted_label=label,
                    confidence=float(confidence),
                    is_duplicate=is_duplicate,
                    is_near_duplicate=is_near_duplicate,
                    reply_text=reply_text
                )
                self.db_writer.insert_reply(tweet_id, reply_text)
                processed_count += 1
                logger.info(f"Stored tweet for user {user_id}: {label} (confidence={confidence:.3f})")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in Kafka record: {e}")
            except Exception as e:
                logger.error(f"Failed processing record: {e}")

        # Metrics for this batch
        self.db_writer.insert_metric("processed_count", processed_count, batch_id=str(epoch_id))
        self.db_writer.insert_metric("duplicate_count", duplicate_count, batch_id=str(epoch_id))
        self.db_writer.insert_metric("near_duplicate_count", near_duplicate_count, batch_id=str(epoch_id))
        self.db_writer.insert_metric("low_confidence_count", low_confidence_count, batch_id=str(epoch_id))

    def process_stream(self, kafka_broker: str = None, topic: str = None):
        """Process Kafka stream.

        Args:
            kafka_broker: Kafka broker address
            topic: Kafka topic to consume
        """
        kafka_broker = kafka_broker or os.getenv('KAFKA_BROKER', 'localhost:9092')
        topic = topic or os.getenv('KAFKA_TOPIC', 'raw_tweets')
        checkpoint_dir = os.getenv('SPARK_CHECKPOINT_DIR', '/tmp/spark-checkpoint')

        os.makedirs(checkpoint_dir, exist_ok=True)

        df = self.spark \
            .readStream \
            .format('kafka') \
            .option('kafka.bootstrap.servers', kafka_broker) \
            .option('subscribe', topic) \
            .option('startingOffsets', 'earliest') \
            .load()

        query = df \
            .writeStream \
            .foreachBatch(self._process_batch) \
            .option('checkpointLocation', checkpoint_dir) \
            .start()

        query.awaitTermination()

    def close(self):
        """Close Spark session and database connection."""
        self.db_writer.close()
        self.spark.stop()


def main():
    processor = StreamProcessor()
    try:
        processor.process_stream()
    except KeyboardInterrupt:
        logger.info("Spark streaming interrupted by user")
    finally:
        processor.close()


if __name__ == '__main__':
    main()
