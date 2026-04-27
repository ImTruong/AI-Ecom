"""
Outbox Service - handles storing events in outbox table
"""
from typing import Dict, Any
from .models import OutboxMessage
from django.db import transaction
import sys
import os

# Add shared to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from events.event_base import Event, EventType


class OutboxService:
    """Service to manage outbox messages"""
    
    @staticmethod
    @transaction.atomic
    def save_event(event: Event) -> 'OutboxMessage':
        """
        Save event to outbox table within a transaction.
        This ensures that business logic and event are saved atomically.
        
        Args:
            event: Event object to save
        
        Returns:
            OutboxMessage instance
        """
        from .models import OutboxMessage
        outbox_message = OutboxMessage.objects.create(
            event_id=event.event_id,
            event_type=event.event_type.value,
            aggregate_id=event.aggregate_id,
            payload={
                'data': event.data,
                'timestamp': event.timestamp,
            },
            correlation_id=event.correlation_id
        )
        return outbox_message
    
    @staticmethod
    def get_pending_messages(limit: int = 100):
        """
        Get pending messages to publish
        
        Args:
            limit: Maximum number of messages to retrieve
        
        Returns:
            QuerySet of pending OutboxMessage instances
        """
        from .models import OutboxMessage
        return OutboxMessage.objects.filter(
            status=OutboxMessage.Status.PENDING
        ).order_by('created_at')[:limit]
    
    @staticmethod
    def get_failed_messages_for_retry(limit: int = 100):
        """
        Get failed messages that haven't exceeded max retries
        
        Args:
            limit: Maximum number of messages to retrieve
        
        Returns:
            QuerySet of failed OutboxMessage instances eligible for retry
        """
        from .models import OutboxMessage
        from django.db import models
        return OutboxMessage.objects.filter(
            status=OutboxMessage.Status.FAILED,
            retry_count__lt=models.F('max_retries')
        ).order_by('last_retry_at')[:limit]


def create_outbox_event_and_save(event_type: EventType, aggregate_id: str, 
                                  data: Dict[str, Any], 
                                  correlation_id: str = None):
    """
    Helper function to create an event and save it to outbox
    
    Usage in service:
        from shared.outbox import create_outbox_event_and_save
        from shared.events import EventType
        
        # In your service method (within transaction)
        outbox_message = create_outbox_event_and_save(
            event_type=EventType.CUSTOMER_REGISTERED,
            aggregate_id=str(customer.id),
            data={'email': customer.email, 'name': customer.name}
        )
    
    Args:
        event_type: Type of event
        aggregate_id: ID of the aggregate (e.g., customer ID)
        data: Event data
        correlation_id: Optional correlation ID
    
    Returns:
        OutboxMessage instance
    """
    event = Event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        data=data,
        correlation_id=correlation_id
    )
    return OutboxService.save_event(event)
