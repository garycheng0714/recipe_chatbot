import opencc
from pydantic_ai import Agent, ModelSettings
from pydantic_ai_harness import InputGuardrail
from pydantic_ai_harness.guardrails.detectors import blocked_keywords

from app.agent.chat_model import generation_model, INJECTION_MARKERS


class GenerationAgent:
    def __init__(self):
        self.agent = Agent(
            model=generation_model,
            model_settings=ModelSettings(temperature=0.0),
            capabilities=[
                InputGuardrail(guard=blocked_keywords(INJECTION_MARKERS))
            ],
            instructions=(
                """
                你是一個根據提供資料回答問題的助手。
                
                規則:
                1. 只根據提供的內容回答,不要使用你自己的知識補充
                2. 如果提供的內容不足以回答問題時,請回答「根據提供的資料無法回答這個問題」,不要猜測或編造
                3. 回答時可以補充上下文,直接回答問題本身,不要重複問題
                4. 回答只有一行時，開頭不要用編號
                5. 用中文回答
                """
            ),
        )

    async def run(self, chunks: list[str], query_text: str):
        if not chunks:
            return "很抱歉，我無法回答這個問題"

        # print(self.build_user_prompt(chunks, query_text))

        result = await self.agent.run(self.build_user_prompt(chunks, query_text))

        converter = opencc.OpenCC('s2twp.json')  # 簡體→繁體(台灣用語+慣用詞)
        zh_tw_text = converter.convert(result.output)

        # print(result.output)

        return zh_tw_text

    def build_user_prompt(self, chunks: list[str], query: str) -> str:
        context = "\n\n".join(f"* {c}" for c in chunks)
        return f"以下是檢索到的相關內容片段:\n\n---\n{context}\n---\n\n問題:{query}"

