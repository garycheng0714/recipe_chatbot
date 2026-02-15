from pydantic import BaseModel, HttpUrl

class DetailUrl(BaseModel):
    url: HttpUrl