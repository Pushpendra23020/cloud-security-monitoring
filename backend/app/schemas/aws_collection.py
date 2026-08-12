from pydantic import BaseModel


class EC2CollectionRequest(BaseModel):
    cloud_account_id: int


class EC2CollectionResponse(BaseModel):
    collected: int
    stored: int
