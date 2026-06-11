from pydantic import BaseModel, ConfigDict


class HybridSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    ingredients: list
    seasoning: list | None
    quantity: int
    steps: str
    description: str
    tags: list
    category: str
    quantity: str