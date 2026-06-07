from tracking_app.application.dto import event_input_from_payload
from tracking_app.domain.repositories import TrackingRepository


class TrackingUseCases:
    def __init__(self, repository: TrackingRepository):
        self.repository = repository

    def record_event(self, payload: dict):
        return self.repository.record_event(event_input_from_payload(payload))

