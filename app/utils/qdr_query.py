import asyncio

from app.client import embed_client, qdr_client
from app.repositories import QdrantRepository

async def main():
    repo = QdrantRepository(qdr_client, embed_client)

    result = await repo.scroll("id", "pork-belly-and-daikon-radish-in-lemon-miso-stew。")

    ids_to_delete = [r.id for r in result[0]]

    await repo.delete_by_point_id(ids_to_delete)

if '__main__' == __name__:
    asyncio.run(main())