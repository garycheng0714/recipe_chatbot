from typing import Protocol

from FlagEmbedding import BGEM3FlagModel

class Embedder(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class BGEEmbedder:
    def __init__(self):
        self.model = BGEM3FlagModel('BAAI/bge-m3',use_fp16=False)

    def embed(self, text: str) -> list[float]:
        output = self.model.encode(
            text.strip(),
            return_dense=True
        )

        return output["dense_vecs"].tolist()