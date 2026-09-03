from dataclasses import dataclass

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, ModelSettings
from pydantic_ai_harness import InputGuardrail
from pydantic_ai_harness.guardrails.detectors import blocked_keywords

from app.agent.chat_model import INJECTION_MARKERS, gemini_model
from app.domain.api_chat import ChatResponse
from app.services.rag_service import RagService


@dataclass
class MainAgentDeps:
    retrieval_service: RagService


agent = Agent(
    model=gemini_model,
    deps_type=MainAgentDeps,
    output_type=ChatResponse,
    model_settings=ModelSettings(temperature=0.0),
    capabilities=[
        InputGuardrail(guard=blocked_keywords(INJECTION_MARKERS))
    ],
    instructions=(
        """
        您是一名助手，負責解答有關 Eliud Kipchoge 及其訪談的問題。

        您可以存取一個知識庫，其中包含從 Eliud Kipchoge 訪談中提取的資訊。

        當使用者的問題需要從知識庫中尋找資訊時，請使用 search_knowledge 工具。

        如果您無需知識庫中的資訊即可回答問題，請直接回答。

        使用檢索到的資訊時，請根據檢索到的上下文作答，切勿捏造事實。
        """
    )
)


@agent.tool
async def search_knowledge(ctx: RunContext[MainAgentDeps], query: str) -> ChatResponse:
    return await ctx.deps.retrieval_service.execute(query)
