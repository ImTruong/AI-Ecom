"""
Robust Customer Event Consumer - Refactored for Reliability
Handles syncing customer data from the Auth service to the Customer service.
"""
import os
import sys
import json
import logging
import time
import django
from django.db import transaction

# 1. SETUP ENVIRONMENT
# Add current and parent directories to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, '..'))
sys.path.insert(0, os.path.join(BASE_DIR, '..', '..', '..', 'shared'))

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'customer_service.settings')
django.setup()

from customer_app.models import Customer
import pika

# 2. LOGGING CONFIGURATION
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CustomerConsumer")


class RobustCustomerConsumer:
    """Production-grade event consumer with automatic retries and robust mapping"""
    
    def __init__(self, rabbitmq_url):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = 'customer_service_sync_queue'
        self.exchange_name = 'ecommerce_events'
        self.connection = None
        self.channel = None

    def connect(self):
        """Handle connection logic with exponential backoff"""
        attempts = 0
        while not self.connection:
            try:
                attempts += 1
                logger.info(f"Connecting to RabbitMQ at {self.rabbitmq_url} (Attempt {attempts})")
                self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
                self.channel = self.connection.channel()
                
                # Ensure exchange exists
                self.channel.exchange_declare(
                    exchange=self.exchange_name,
                    exchange_type='topic',
                    durable=True
                )
                
                # Ensure queue exists
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                
                # Listen for all customer-related events
                self.channel.queue_bind(
                    exchange=self.exchange_name,
                    queue=self.queue_name,
                    routing_key='customer.*'
                )
                
                logger.info("✅ Connection established and queue bound.")
                return True
            except Exception as e:
                logger.error(f"❌ Connection failed: {e}")
                if attempts > 10:
                    logger.critical("Maximum connection attempts reached. Exiting.")
                    return False
                time.sleep(min(attempts * 2, 30))
        return False

    def on_message(self, ch, method, properties, body):
        """Process incoming RabbitMQ messages"""
        try:
            event = json.loads(body)
            event_type = event.get('event_type')
            
            # Extract data - cover all possible wrapper names
            data = event.get('data') or event.get('payload') or event
            
            logger.info(f"📥 Received event: {event_type}")
            
            if event_type in ['customer.registered', 'customer.created']:
                self.sync_customer(data)
            elif event_type == 'customer.updated':
                self.update_customer(data)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"⚠️ Error processing message: {str(e)}")
            # Reject and requeue on transient failures
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def sync_customer(self, data):
        """Synchronize a new customer record"""
        # CRITICAL: Robust ID mapping
        # Auth Service sends 'customer_id' in its data payload
        auth_id = data.get('customer_id') or data.get('user_id') or data.get('id')
        email = data.get('email')
        
        if not auth_id or not email:
            logger.error(f"🚫 Cannot sync customer: Missing ID ({auth_id}) or Email ({email})")
            return

        try:
            with transaction.atomic():
                customer, created = Customer.objects.update_or_create(
                    auth_customer_id=auth_id,
                    defaults={
                        'email': email,
                        'full_name': data.get('full_name', ''),
                        'phone': data.get('phone', ''),
                        'address': data.get('address', ''),
                        'is_active': data.get('is_active', True)
                    }
                )
                action = "Created" if created else "Updated (Sync)"
                logger.info(f"✨ {action} customer: {email} (AuthID: {auth_id})")
        except Exception as e:
            logger.error(f"🔥 Database error syncing customer: {e}")
            raise # Propagate to trigger NACK

    def update_customer(self, data):
        """Update existing customer record"""
        auth_id = data.get('customer_id') or data.get('user_id') or data.get('id')
        if not auth_id: return

        try:
            Customer.objects.filter(auth_customer_id=auth_id).update(
                full_name=data.get('full_name', ''),
                phone=data.get('phone', ''),
                address=data.get('address', ''),
                updated_at=django.utils.timezone.now()
            )
            logger.info(f"📝 Updated customer AuthID: {auth_id}")
        except Exception as e:
            logger.error(f"🔥 Error updating customer: {e}")

    def run(self):
        """Start the main consumption loop"""
        if not self.connect():
            return
            
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.on_message
            )
            logger.info("🚀 Waiting for events...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"💀 Fatal consumer error: {e}")
            self.stop()

    def stop(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔌 Connection closed.")


if __name__ == '__main__':
    RMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://admin:admin123@rabbitmq:5672/')
    RobustCustomerConsumer(RMQ_URL).run()
