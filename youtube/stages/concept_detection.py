from app.database import AsyncSessionLocal
from typing import List
import json, os

from pydantic import TypeAdapter

from app.repositories.yt_repository import YtRepository
from app.services.concept_detection import ConceptDetection
from youtube.domain.golden_set import SectionData
from youtube.domain.video_document import VideoDocument


class ConceptDetectionStage:
    def __init__(
        self,
        detector: ConceptDetection = ConceptDetection(),
        yt_repository: YtRepository = YtRepository(),
        session_factory=AsyncSessionLocal
    ):
        self.detector = detector
        self.yt_repository = yt_repository
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:

        with open(f"{os.getcwd()}/youtube/golden_set/ef78a47c-652c-5eaa-a7fc-08d3ee5fdd86.json", "r") as f:
            json_data = json.load(f)
            golden_set = TypeAdapter(List[SectionData]).validate_python(json_data)

        for section in golden_set:
            async with self.session_factory() as session:
                chunks = await self.yt_repository.fetch_chunks_by_section_id(session, section.section_id)

            if len(chunks) == 0:
                continue

            for concept in section.important_concepts:
                detect_result = self.detector.detect(chunks, concept.concept_text)

                print(f"concept: {concept}")
                for r in detect_result:
                    print(f"entailment score: {r.entailment_score}")
                    # if 0.9 > r.entailment_score > 0.5:
                    #     print(r.premise)
                print("-----------")


        return VideoDocument()