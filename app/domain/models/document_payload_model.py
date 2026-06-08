from pydantic import BaseModel


class DocumentPayload(BaseModel):
    ...


class RecipeDocumentPayload(DocumentPayload):
    id: str
    name: str
    category: str
    description: str
    quantity: str | None
    ingredients: list[str] | None
    seasoning: list[str] | None
    steps: str
    tags: list[str]