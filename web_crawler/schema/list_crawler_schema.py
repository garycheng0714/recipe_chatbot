from pydantic import BaseModel, HttpUrl

class DetailUrl(BaseModel):
    url: HttpUrl

    def get_url(self) -> str:
        return str(self.url)