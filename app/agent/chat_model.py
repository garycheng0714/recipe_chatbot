from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    model_name='llama3:8b',
    provider=OpenAIProvider(base_url='http://localhost:11434/v1'),
)