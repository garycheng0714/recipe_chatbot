from dataclasses import dataclass
from typing import Union

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelSettings, UsageLimits
from pydantic_ai_harness import InputGuardrail
from pydantic_ai_harness.guardrails.detectors import blocked_keywords

from app.agent.chat_model import INJECTION_MARKERS, GEMINI_MODEL, ORNITH_MODEL, QWEN_MODEL
from app.domain.api_chat import ChatResponse
from app.route.domain.model import RouteSearchRequest, NeedsClarification
from app.services.rag_service import RagService


logfire.configure()
logfire.instrument_system_metrics()
logfire.instrument_pydantic_ai()





class RouteService:
    async def search(self, query: RouteSearchRequest) -> str:
        return "陽明山十連峰"



@dataclass
class MainAgentDeps:
    retrieval_service: RagService
    route_service: RouteService


main_agent = Agent(
    model=GEMINI_MODEL,
    deps_type=MainAgentDeps,
    output_type=Union[ChatResponse, NeedsClarification],
    # output_type=ChatResponse,
    # model_settings=ModelSettings(temperature=0.0),
    capabilities=[
        InputGuardrail(guard=blocked_keywords(INJECTION_MARKERS))
    ],
    instructions=(
        """
        您是一名助手，負責回答問題

        1. 如果您無需透過工具獲取資訊即可回答問題，請直接回答。
        2. 使用檢索獲得資訊時，請直接使用檢索到的資料回答，切勿捏造事實或額外補充。
        3. 資訊不足時不要猜測數字、不要假設,回傳 NeedsClarification 詢問使用者。
        """
    )
)


@main_agent.tool(retries=1)
async def get_interview_information(ctx: RunContext[MainAgentDeps], query: str) -> ChatResponse:
    """獲取 Eliud Kipchoge 的相關資訊

    【適用情境】當使用者詢問有關 Eliud Kipchoge 的相關問題時
    """
    result = await ctx.deps.retrieval_service.execute(query)
    return result


@main_agent.tool(retries=1)
async def get_trail_route_information(ctx: RunContext[MainAgentDeps], query: RouteSearchRequest) -> str:
    """查詢具體的越野跑路線與步道資訊

    【適用情境】當使用者詢問特定地點、距離（km）、爬升量（m）、路線規劃或具體步道名稱時
    """
    return await ctx.deps.route_service.search(query)