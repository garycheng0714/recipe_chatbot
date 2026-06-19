from abc import ABC, abstractmethod


class BasePrompt(ABC):

    @abstractmethod
    def render(self, content: str) -> str:
        ...