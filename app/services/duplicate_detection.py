import asyncio
import itertools

from qdrant_client.conversions.common_types import Record

from app.client import qdr_client, embed_client
from app.inference.nli.classifier import NLIClassifier
from app.infrastructure.qdrant.config import YtQdrantSetting
from app.repositories import QdrantRepository


class DuplicateDetection:
    def __init__(
        self,
        qdrant: QdrantRepository = QdrantRepository(YtQdrantSetting(), qdr_client, embed_client),
        classifier: NLIClassifier = NLIClassifier(),
        collection_name: str = "yt_interview",
        max_concurrency: int = 20,
    ):
        self.qdrant = qdrant
        self.classifier = classifier
        self.collection_name = collection_name
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def detect(self):
        candidates = await self._find_duplicate_candidates()

        pairs = [(r["point_payload"]["answer"], r["match_payload"]["answer"]) for r in candidates]

        nli_result = self.classifier.classify_bidirectional_batch(pairs)

        for r in nli_result:
            if r.both_entailment:
                print(r.min_entailment_score)
                print(r.text_a)
                print(r.text_b)
                print('---------------')


    async def _find_duplicate_candidates(self):
        all_points = await self.qdrant.find_all_points()

        tasks = [self.find_near_duplicates(p) for p in all_points]

        result = await asyncio.gather(*tasks)

        flattened_result = list(itertools.chain.from_iterable(result))

        return self._deduplicate_candidates(flattened_result)

    def _deduplicate_candidates(self, candidates: list):
        deduped = {}
        for item in candidates:
            pair_key = tuple(sorted([str(item["point_id"]), str(item["match_id"])]))

            # 若同一 pair 出現兩次，保留分數較高者
            if pair_key not in deduped or item["score"] > deduped[pair_key]["score"]:
                deduped[pair_key] = item

        return list(deduped.values())


    async def find_near_duplicates(self, point: Record, threshold: float = 0.92, query_limit: int = 10):
        duplicates = []

        async with self.semaphore:
            results = await self.qdrant.query_points_by_vector(vector=point.vector["dense"], limit=query_limit)

        for r in results.points:
            if r.id == point.id:
                continue
            if r.score < threshold:
                continue

            duplicates.append(
                {
                    "point_id": point.id,
                    "match_id": r.id,
                    "score": r.score,
                    "point_payload": point.payload,
                    "match_payload": r.payload,
                }
            )

        return duplicates

if __name__ == "__main__":
    async def main():
        detector = DuplicateDetection()
        await detector.detect()

    asyncio.run(main())