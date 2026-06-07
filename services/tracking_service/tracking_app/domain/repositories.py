from abc import ABC, abstractmethod


class TrackingRepository(ABC):
    @abstractmethod
    def record_event(self, event_input):
        raise NotImplementedError

