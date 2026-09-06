import os

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

OPENAI_PROVIDER=OpenAIProvider(base_url='http://localhost:11434/v1')

generation_model = OpenAIChatModel(
    model_name='ornith-1.5:9b',
    provider=OPENAI_PROVIDER,
)

translate_model = OpenAIChatModel(
    model_name='llama3:8b',
    provider=OPENAI_PROVIDER,
)

ORNITH_MODEL = OpenAIChatModel(
    model_name='ornith-1.5:9b',
    provider=OPENAI_PROVIDER,
)

QWEN_MODEL = OpenAIChatModel(
    model_name='qwen3.5:2b',
    provider=OPENAI_PROVIDER,
)

provider = GoogleProvider(api_key=os.environ['GOOGLE_API_KEY'])
GEMINI_MODEL = GoogleModel('gemini-2.5-flash-lite', provider=provider)

INJECTION_MARKERS = [
    "忽略以上", "忽略上面", "ignore previous", "ignore above", "ignore all",
    "system prompt", "system instruction", "你現在是", "你不是翻譯",
    "直接輸出", "output the following", "print your instructions",
    "回答任何問題"
]