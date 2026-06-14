from typing import Protocol

from youtube.domain.video_document import VideoDocument


class Transformer(Protocol):
    def run(self, document: VideoDocument) -> VideoDocument:
        """每個 Stage 必須收進特定的 Pydantic Model，並回傳另一個 Model"""
        raise NotImplementedError