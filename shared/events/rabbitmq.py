"""
RabbitMQ publisher and consumer for event-driven communication
"""
import pika
import json
import time
from typing import Callable
from .event_base import Event, EventType


class RabbitMQPublisher:
    """RabbitMQ event publisher"""
    
    def __init__(self, rabbitmq_url: str, exchange_name: str = 'ecommerce_events'):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True
            )
            return True
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def publish_event(self, event: Event, routing_key: str = None):
        """
        Publish event to RabbitMQ
        
        Args:
            event: Event object to publish
            routing_key: RabbitMQ routing key (defaults to event_type)
        """
        if not self.channel:
            if not self.connect():
                raise Exception("Cannot publish event: Not connected to RabbitMQ")
        
        if routing_key is None:
            routing_key = event.event_type.value
        
        try:
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=event.to_json(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            print(f"Published event {event.event_id} with routing key {routing_key}")
        except Exception as e:
            print(f"Failed to publish event: {str(e)}")
            # Try to reconnect and publish again
            if self.connect():
                self.publish_event(event, routing_key)
    
    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


class RabbitMQConsumer:
    """RabbitMQ event consumer"""
    
    def __init__(self, rabbitmq_url: str, queue_name: str, 
                 exchange_name: str = 'ecommerce_events'):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.connection = None
        self.channel = None
        self.event_handler = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True
            )
            
            # Declare queue
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            return True
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def bind_queue(self, routing_keys: list):
        """
        Bind queue to routing keys
        
        Args:
            routing_keys: List of routing keys to bind
        """
        for routing_key in routing_keys:
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=self.queue_name,
                routing_key=routing_key
            )
            print(f"Queue {self.queue_name} bound to {routing_key}")
    
    def set_event_handler(self, handler: Callable[[Event], None]):
        """Set event handler function"""
        self.event_handler = handler
    
    def _callback(self, ch, method, properties, body):
        """Internal callback for message consumption"""
        try:
            event = Event.from_json(body.decode())
            print(f"Received event {event.event_id}: {event.event_type.value}")
            
            if self.event_handler:
                self.event_handler(event)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            # Negative acknowledgment - requeue the message
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Start consuming messages"""
        if not self.channel:
            if not self.connect():
                raise Exception("Cannot start consuming: Not connected to RabbitMQ")
        
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._callback
        )
        
        print(f"Starting to consume from queue {self.queue_name}")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
