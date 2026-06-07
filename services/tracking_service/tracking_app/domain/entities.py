from dataclasses import dataclass


@dataclass(frozen=True)
class TrackingEventInput:
    event_type: str
    product_id: int
    user_id: int | None = None
    session_id: str | None = None
    product_variant_id: int | None = None
    metadata: dict | None = None

