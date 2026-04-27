"""
Event base classes for microservices communication
"""
import json
from datetime import datetime
from typing import Dict, Any
from enum import Enum


class EventType(Enum):
    """Event types for saga choreography"""
    # Customer events
    CUSTOMER_REGISTERED = "customer.registered"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    
    # Staff events
    STAFF_CREATED = "staff.created"
    STAFF_UPDATED = "staff.updated"
    STAFF_DELETED = "staff.deleted"
    
    # Auth events
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    PASSWORD_CHANGED = "password.changed"


class Event:
    """Base event class"""
    
    def __init__(self, event_type: EventType, aggregate_id: str, data: Dict[str, Any], 
                 correlation_id: str = None):
        self.event_id = self._generate_event_id()
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.data = data
        self.correlation_id = correlation_id or self.event_id
        self.timestamp = datetime.utcnow().isoformat()
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'aggregate_id': self.aggregate_id,
            'data': self.data,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, event_dict: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        event = cls(
            event_type=EventType(event_dict['event_type']),
            aggregate_id=event_dict['aggregate_id'],
            data=event_dict['data'],
            correlation_id=event_dict.get('correlation_id')
        )
        event.event_id = event_dict['event_id']
        event.timestamp = event_dict['timestamp']
        return event
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Create event from JSON string"""
        return cls.from_dict(json.loads(json_str))


class EventHandler:
    """Base class for event handlers"""
    
    def __init__(self):
        self.handlers = {}
    
    def register_handler(self, event_type: EventType, handler_func):
        """Register a handler function for an event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler_func)
    
    def handle_event(self, event: Event):
        """Handle an event by calling registered handlers"""
        event_type = event.event_type
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error handling event {event.event_id}: {str(e)}")
                    # Log error but continue with other handlers
    
    def handle_event_json(self, json_str: str):
        """Handle event from JSON string"""
        event = Event.from_json(json_str)
        self.handle_event(event)
