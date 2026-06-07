from tracking_app.domain.repositories import TrackingRepository
from tracking_app.models import TrackingEvent


class DjangoTrackingRepository(TrackingRepository):
    def record_event(self, event_input):
        return TrackingEvent.objects.create(
            user_id=event_input.user_id,
            session_id=event_input.session_id,
            event_type=event_input.event_type,
            product_id=event_input.product_id,
            product_variant_id=event_input.product_variant_id,
            metadata=event_input.metadata or {},
        )

