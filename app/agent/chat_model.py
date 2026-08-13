from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

generation_model = OpenAIChatModel(
    model_name='llama3-chatqa:8b',
    provider=OpenAIProvider(base_url='http://localhost:11434/v1'),
)

translate_model = OpenAIChatModel(
    model_name='llama3:8b',
    provider=OpenAIProvider(base_url='http://localhost:11434/v1'),
)

INJECTION_MARKERS = [
    "忽略以上", "忽略上面", "ignore previous", "ignore above",
    "system prompt", "system instruction", "你現在是", "你不是翻譯",
    "直接輸出", "output the following", "print your instructions",
    "回答任何問題"
]