from django.db import models
from django.utils import timezone

class Rating(models.Model):
    order_id = models.IntegerField(db_index=True)
    customer_id = models.IntegerField(db_index=True)
    product_type = models.CharField(max_length=20) # book, clothes
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    stars = models.IntegerField() # 1-5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ratings'
        unique_together = ('order_id', 'product_type', 'product_id')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'product_type': self.product_type,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'stars': self.stars,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }
