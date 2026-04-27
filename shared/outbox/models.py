"""
Outbox Pattern implementation for ensuring eventual consistency
"""
from django.db import models
from django.utils import timezone


class OutboxMessage(models.Model):
    """
    Outbox table to store events before publishing to message broker.
    Ensures that database changes and event publishing are atomic.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PUBLISHED = 'published', 'Published'
        FAILED = 'failed', 'Failed'
    
    id = models.AutoField(primary_key=True)
    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=255, db_index=True)
    aggregate_id = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField()
    correlation_id = models.CharField(max_length=255, null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        app_label = 'outbox'
        db_table = 'outbox_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"OutboxMessage({self.event_id}, {self.event_type}, {self.status})"
    
    def mark_as_published(self):
        """Mark message as successfully published"""
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at'])
    
    def mark_as_failed(self, error_message: str):
        """Mark message as failed"""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.last_retry_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'last_retry_at'])
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        self.last_retry_at = timezone.now()
        
        if self.retry_count >= self.max_retries:
            self.status = self.Status.FAILED
        
        self.save(update_fields=['retry_count', 'last_retry_at', 'status'])
