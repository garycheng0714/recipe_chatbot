from app.infrastructure.initializer import get_infra_initializer
import asyncio


async def init_db():
    async with get_infra_initializer() as infra_initializer:
        await infra_initializer.run_all()

if "__main__" == __name__:
    asyncio.run(init_db())