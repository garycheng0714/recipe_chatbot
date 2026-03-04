from abc import ABC, abstractmethod

class BaseRequester(ABC):
    @abstractmethod
    async def request(self, url: str) -> str:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass