import asyncio
import time

import asyncpg
import httpx
import redis.asyncio as redis

from app.database import POSTGRES_DSN, REDIS_URL, EMBED_URL


async def startup():
    await asyncio.gather(
        wait_postgres(),
        wait_redis(),
    )

    await wait_embedding_service()

async def wait_postgres(timeout=10):
    start = time.time()

    delay = 1

    while True:
        if time.time() - start > timeout:
            raise TimeoutError("Postgres not ready")
        try:
            conn = await asyncpg.connect(POSTGRES_DSN)
            await conn.execute("SELECT 1")
            await conn.close()
            print("Postgres ready")
            return
        except Exception as e:
            print(f"Postgres not ready: {e}")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 10)

async def wait_redis():
    delay = 1

    while True:
        try:
            redis_client = await redis.from_url(REDIS_URL)
            await redis_client.ping()
            print("Redis ready")
            return
        except Exception as e:
            print(f"Redis not ready: {e}")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 10)

async def wait_embedding_service():
    delay = 1

    while True:
        try:
            r = httpx.get(f"{EMBED_URL}/health")
            # print(r.json())
            # and r.json().get("model_loaded")
            if r.status_code == 200:
                print("Embedding ready")
                return
        except Exception as e:
            print(f"Embedding Service not ready: {e}")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 10)


if __name__ == '__main__':
    asyncio.run(startup())