import os
import sys
import django
import time
import logging

# Set up logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AuthPublisher")

# 1. SETUP ENVIRONMENT
# Add current and parent directories to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, '..', '..', 'shared'))

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from outbox.polling_publisher import PollingPublisher

class RobustAuthPublisher:
    """Production-grade polling publisher for Auth service"""
    
    def __init__(self, rabbitmq_url):
        self.rabbitmq_url = rabbitmq_url
        self.publisher = PollingPublisher(rabbitmq_url, poll_interval=5)

    def run(self):
        """Start the publisher with retry logic"""
        logger.info(f"Starting Robust Auth Service Polling Publisher at {self.rabbitmq_url}")
        
        while True:
            try:
                # PollingPublisher's start() is blocking and polls every poll_interval
                self.publisher.start()
            except Exception as e:
                logger.error(f"❌ Publisher error: {str(e)}. Attempting restart in 10s...")
                time.sleep(10)

if __name__ == '__main__':
    RMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://admin:admin123@rabbitmq:5672/')
    RobustAuthPublisher(RMQ_URL).run()
