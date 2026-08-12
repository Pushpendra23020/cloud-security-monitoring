from fastapi import HTTPException, status

from app.collectors.aws.sts import (
    AWSConnectionError,
    get_caller_identity,
)


class AWSService:
    @staticmethod
    def verify_connection() -> dict[str, str | bool]:
        try:
            identity = get_caller_identity()

            return {
                "connected": True,
                "account_id": identity["account_id"],
                "arn": identity["arn"],
                "user_id": identity["user_id"],
            }

        except AWSConnectionError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
