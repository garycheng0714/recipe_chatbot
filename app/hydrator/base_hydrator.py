from typing import Protocol, Any


class BaseHydrator(Protocol):
    async def hydrate(self, ids: list[str]) -> list[dict[str, Any]]:
        ...