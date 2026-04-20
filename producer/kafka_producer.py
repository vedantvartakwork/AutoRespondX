"""Kafka producer for streaming CSV data."""

import os
import json
import csv
import time
import logging
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventProducer:
    """Producer for streaming events from CSV to Kafka."""

    def __init__(self, broker: str = None, topic: str = None, delay: float = 1.0):
        """Initialize Kafka producer.
        
        Args:
            broker: Kafka broker address (default from KAFKA_BROKER env var)
            topic: Kafka topic (default from KAFKA_TOPIC env var)
            delay: Delay between messages in seconds
        """
        self.broker = broker or os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.topic = topic or os.getenv('KAFKA_TOPIC', 'raw_tweets')
        self.delay = float(delay)
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[self.broker],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info(f"Connected to Kafka broker: {self.broker}")
            logger.info(f"Target topic: {self.topic}")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def send_event(self, event: Dict[str, Any]) -> bool:
        """Send event to Kafka.
        
        Args:
            event: Event data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.producer.send(self.topic, value=event).get(timeout=10)
            return True
        except KafkaError as e:
            logger.error(f"Error sending event: {e}")
            return False

    def stream_csv(self, csv_path: str):
        """Stream CSV file row by row to Kafka.
        
        Args:
            csv_path: Path to CSV file
        """
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                row_count = 0
                
                for row in reader:
                    if self.send_event(row):
                        row_count += 1
                        logger.info(f"Sent message {row_count}: {row.get('user_id', 'unknown')} - {row.get('message', '')[:50]}...")
                        time.sleep(self.delay)
                    else:
                        logger.warning(f"Failed to send row: {row}")
                
                logger.info(f"Finished streaming {row_count} messages from {csv_path}")
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise

    def close(self):
        """Close producer connection."""
        try:
            self.producer.close()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")


def main():
    """Main entry point for CLI usage."""
    csv_file = os.getenv('CSV_PATH', './data/sample/tweets_sample.csv')
    delay = float(os.getenv('MESSAGE_DELAY_SECONDS', 1.0))
    
    logger.info(f"Starting producer with delay={delay}s")
    
    producer = EventProducer(delay=delay)
    try:
        producer.stream_csv(csv_file)
    except KeyboardInterrupt:
        logger.info("Producer interrupted by user")
    except Exception as e:
        logger.error(f"Producer error: {e}")
    finally:
        producer.close()


if __name__ == '__main__':
    main()
