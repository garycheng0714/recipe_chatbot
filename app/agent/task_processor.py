import asyncio

from pydantic_ai import Agent

class TaskProcessor:
    def __init__(self, agent: Agent, concurrency: int = 5):
        self.agent = agent
        self.semaphore = asyncio.Semaphore(concurrency)

    async def process(self, prompt: str):
        async with self.semaphore:
            result = await self.agent.run(prompt)
            return result.output

    async def process_all(self, prompts: list[str]):
        return await asyncio.gather(
            *(self.process(p) for p in prompts)
        )