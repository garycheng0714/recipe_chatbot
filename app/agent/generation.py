from pydantic_ai import Agent, ModelSettings

from app.agent.chat_model import model


class GenerationAgent:
    def __init__(self):
        self.agent = Agent(
            model=model,    # "gemini-2.5-flash"
            model_settings=ModelSettings(temperature=0.0),
            system_prompt=(
                "你是一個根據提供資料回答問題的助手。\n"
                "規則:\n"
                "1. 只根據提供的內容回答,不要使用你自己的知識補充\n"
                "2. 如果提供的內容不足以回答問題,請明確說「根據提供的資料無法回答這個問題」,不要猜測或編造\n"
                "3. 回答時保持簡潔,直接回答問題本身,不要重複問題"
            ),
        )

    async def run(self, chunks: list, query_text: str):
        result = await self.agent.run(self.build_user_prompt(chunks, query_text))
        return result.output

    def build_user_prompt(self, chunks: list[str], query: str) -> str:
        context = "\n\n".join(f"* {c}" for i, c in enumerate(chunks))
        return f"以下是檢索到的相關內容片段:\n\n---\n{context}\n---\n\n問題:{query}"

