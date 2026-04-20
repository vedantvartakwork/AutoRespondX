"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Histogram, Gauge


class Metrics:
    """Metrics collection for observability."""

    def __init__(self):
        """Initialize metrics."""
        self.events_processed = Counter(
            'events_processed_total',
            'Total events processed',
            ['event_type']
        )

        self.processing_duration = Histogram(
            'event_processing_duration_seconds',
            'Event processing duration'
        )

        self.duplicates_detected = Counter(
            'duplicates_detected_total',
            'Total duplicates detected'
        )

        self.active_connections = Gauge(
            'active_connections',
            'Active Kafka connections'
        )

        self.prediction_accuracy = Gauge(
            'prediction_accuracy',
            'Model prediction accuracy'
        )

    def record_event(self, event_type: str, duration: float):
        """Record event processing.
        
        Args:
            event_type: Type of event
            duration: Processing duration
        """
        self.events_processed.labels(event_type=event_type).inc()
        self.processing_duration.observe(duration)

    def record_duplicate(self):
        """Record duplicate detection."""
        self.duplicates_detected.inc()

    def set_connections(self, count: int):
        """Set active connections.
        
        Args:
            count: Number of connections
        """
        self.active_connections.set(count)

    def set_accuracy(self, accuracy: float):
        """Set prediction accuracy.
        
        Args:
            accuracy: Accuracy value 0-1
        """
        self.prediction_accuracy.set(accuracy)
