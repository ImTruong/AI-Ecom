"""
Polling Publisher - polls outbox table and publishes events to RabbitMQ
"""
import time
import sys
import os
from typing import Optional

# Add shared to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from events.event_base import Event, EventType
from events.rabbitmq import RabbitMQPublisher


class PollingPublisher:
    """
    Polls outbox table and publishes pending events to RabbitMQ.
    Runs as a background process.
    """
    
    def __init__(self, rabbitmq_url: str, poll_interval: int = 5):
        """
        Initialize polling publisher
        
        Args:
            rabbitmq_url: RabbitMQ connection URL
            poll_interval: Polling interval in seconds
        """
        self.publisher = RabbitMQPublisher(rabbitmq_url)
        self.poll_interval = poll_interval
        self.running = False
    
    def start(self):
        """Start polling and publishing"""
        self.running = True
        
        # Connect to RabbitMQ
        if not self.publisher.connect():
            print("Failed to connect to RabbitMQ. Retrying...")
            time.sleep(5)
            return self.start()
        
        print(f"Polling publisher started. Polling every {self.poll_interval} seconds.")
        
        while self.running:
            try:
                self._poll_and_publish()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"Error in polling publisher: {str(e)}")
                time.sleep(self.poll_interval)
    
    def stop(self):
        """Stop polling"""
        self.running = False
        self.publisher.close()
        print("Polling publisher stopped.")
    
    def _poll_and_publish(self):
        """Poll outbox table and publish pending messages"""
        from .service import OutboxService
        pending_messages = OutboxService.get_pending_messages(limit=100)
        
        if not pending_messages:
            return
        
        print(f"Found {len(pending_messages)} pending messages to publish")
        
        for outbox_message in pending_messages:
            try:
                self._publish_message(outbox_message)
            except Exception as e:
                print(f"Failed to publish message {outbox_message.event_id}: {str(e)}")
                outbox_message.increment_retry()
    
    def _publish_message(self, outbox_message: 'OutboxMessage'):
        """
        Publish a single outbox message to RabbitMQ
        
        Args:
            outbox_message: OutboxMessage instance to publish
        """
        # Reconstruct event from outbox message
        event = Event(
            event_type=EventType(outbox_message.event_type),
            aggregate_id=outbox_message.aggregate_id,
            data=outbox_message.payload['data'],
            correlation_id=outbox_message.correlation_id
        )
        event.event_id = outbox_message.event_id
        event.timestamp = outbox_message.payload['timestamp']
        
        # Publish to RabbitMQ
        try:
            self.publisher.publish_event(event)
            outbox_message.mark_as_published()
            print(f"Published event {event.event_id}")
        except Exception as e:
            error_msg = f"Failed to publish: {str(e)}"
            print(error_msg)
            
            # Increment retry or mark as failed
            if outbox_message.retry_count + 1 >= outbox_message.max_retries:
                outbox_message.mark_as_failed(error_msg)
            else:
                outbox_message.increment_retry()


def run_polling_publisher(rabbitmq_url: str, poll_interval: int = 5):
    """
    Helper function to run polling publisher
    
    Usage:
        python manage.py run_polling_publisher
    
    Args:
        rabbitmq_url: RabbitMQ connection URL
        poll_interval: Polling interval in seconds
    """
    publisher = PollingPublisher(rabbitmq_url, poll_interval)
    try:
        publisher.start()
    except KeyboardInterrupt:
        publisher.stop()
