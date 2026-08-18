from googletrans import Translator
from fastapi import HTTPException

from app.agent.generation import GenerationAgent
from app.agent.translate import TranslateAgent
from app.services.retriever_service import RetrievalService


class RagService:
    def __init__(
        self,
        translate_agent: TranslateAgent,
        generation_agent: GenerationAgent,
        retrieval_service: RetrievalService,
        translator: Translator
    ):
        self.translate_agent = translate_agent
        self.generation_agent = generation_agent
        self.retrieval_service = retrieval_service
        self.translator = translator

    async def execute(self, query_text: str) -> str:
        question = await self.translate_agent.run(query_text)

        retrieval_results = await self.retrieval_service.retrieve(question, 5)

        # 安全檢查：找不到就報 404，不要讓後續程式碼崩潰
        if not len(retrieval_results):
            raise HTTPException(status_code=404, detail="Data not found")

        answers = [r.answer for r in retrieval_results]

        translated_answers = [
            translated_text.text
            for translated_text in await self.translator.translate(answers, dest='zh-tw')
        ]

        result = await self.generation_agent.run(
            translated_answers,
            question
        )

        return result


