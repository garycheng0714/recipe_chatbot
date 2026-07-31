from abc import ABC, abstractmethod


class BaseMetrics(ABC):

    @property
    @abstractmethod
    def criteria(self) -> float:
        ...

    @property
    @abstractmethod
    def metrics_name(self) -> str:
        ...

    @staticmethod
    @abstractmethod
    def calculate(relevant_ids: list[str], result_ids: list[str]) -> float:
        ...

