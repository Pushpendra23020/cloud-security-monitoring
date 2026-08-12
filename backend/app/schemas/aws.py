from pydantic import BaseModel


class AWSIdentityResponse(BaseModel):
    connected: bool
    account_id: str
    arn: str
    user_id: str
