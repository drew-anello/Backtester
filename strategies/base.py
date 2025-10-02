from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bar) -> dict:
        """Return target weights or desired orders."""
