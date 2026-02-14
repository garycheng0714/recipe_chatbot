from abc import ABC, abstractmethod

class BaseRequester(ABC):
    @abstractmethod
    def request(self, url: str) -> str:
        pass