import asyncio
from typing import Set, Dict, List, Optional

from qdrant_client import AsyncQdrantClient
from elasticsearch import AsyncElasticsearch


class QdrantESDiffChecker:
    def __init__(
        self,
        qdrant_url: str,
        es_url: str,
        collection: str,
        es_index: str,
        id_field: str = "recipe_id",
    ):
        self.qdrant = AsyncQdrantClient(url=qdrant_url)
        self.es = AsyncElasticsearch(hosts=[es_url])

        self.collection = collection
        self.es_index = es_index
        self.id_field = id_field

    # ----------------------------
    # 1. 取 Qdrant 全部 IDs
    # ----------------------------
    async def fetch_qdrant_ids(self) -> Set[str]:
        ids = set()
        offset = None

        while True:
            points, offset = await self.qdrant.scroll(
                collection_name=self.collection,
                limit=256,
                offset=offset,
                with_payload=[self.id_field],
                with_vectors=False,
            )

            for p in points:
                val = (p.payload or {}).get(self.id_field)
                if val:
                    ids.add(str(val))

            if offset is None:
                break

        return ids

    # ----------------------------
    # 2. 取 ES 全部 IDs (scroll)
    # ----------------------------
    async def fetch_es_ids(self) -> Set[str]:
        ids = set()

        resp = await self.es.search(
            index=self.es_index,
            scroll="2m",
            size=500,
            query={"match_all": {}},
        )

        scroll_id = resp["_scroll_id"]

        while True:
            hits = resp["hits"]["hits"]
            if not hits:
                break

            for h in hits:
                ids.add(h["_source"]["id"])

            resp = await self.es.scroll(
                scroll_id=scroll_id,
                scroll="2m",
            )

            scroll_id = resp["_scroll_id"]

        return ids

    # ----------------------------
    # 3. diff logic
    # ----------------------------
    async def run_diff(self):
        qdrant_ids, es_ids = await asyncio.gather(
            self.fetch_qdrant_ids(),
            self.fetch_es_ids(),
        )

        only_in_qdrant = qdrant_ids - es_ids
        only_in_es = es_ids - qdrant_ids

        print("\n===== DIFF RESULT =====")
        print(f"Qdrant IDs: {len(qdrant_ids)}")
        print(f"ES IDs: {len(es_ids)}")

        print(f"\n❗ Only in Qdrant: {len(only_in_qdrant)}")
        print(list(only_in_qdrant)[:20])

        print(f"\n❗ Only in ES: {len(only_in_es)}")
        print(list(only_in_es)[:20])

        return {
            "only_in_qdrant": only_in_qdrant,
            "only_in_es": only_in_es,
        }

    async def close(self):
        await self.qdrant.close()
        await self.es.close()


# ----------------------------
# CLI entry
# ----------------------------
async def main():
    checker = QdrantESDiffChecker(
        qdrant_url="http://localhost:6333",
        es_url="http://localhost:9200",
        collection="recipes",
        es_index="recipes",
        id_field="id",
    )

    try:
        await checker.run_diff()
    finally:
        await checker.close()


if __name__ == "__main__":
    asyncio.run(main())