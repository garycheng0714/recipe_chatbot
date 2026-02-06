from pydantic_ai import ModelSettings, Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from app.agent.prompts import router_prompt
from app.schema.ai_schemas import IntentResult

_assistant_model = OpenAIChatModel(
    model_name='qwen2.5:1.5b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
    settings=ModelSettings(
        temperature=0,
    )
)

router_agent = Agent(
    model=_assistant_model,
    model_settings=ModelSettings(temperature=0),
    retries=0,
    output_type=IntentResult,
    system_prompt=router_prompt
)