from sentence_transformers import CrossEncoder

from app.retriever.model import RerankResult

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


class Rerank:

    @staticmethod
    def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[RerankResult]:
        pairs = [(query, chunk['answer']) for chunk in chunks]
        scores = reranker.predict(pairs)

        scored_chunks = [
            {
                **chunk,
                'rerank_score': float(score)
            }
            for chunk, score in zip(chunks, scores)
        ]
        scored_chunks.sort(key=lambda c: c['rerank_score'], reverse=True)

        return [
            RerankResult.model_validate(chunk)
            for chunk in scored_chunks[:top_k]
        ]