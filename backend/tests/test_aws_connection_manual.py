from app.collectors.aws.sts import (
    AWSConnectionError,
    get_caller_identity,
)


def main() -> None:
    try:
        identity = get_caller_identity()

        print("AWS connection successful")
        print(f"Account: {identity['account_id']}")
        print(f"ARN: {identity['arn']}")
        print(f"User ID: {identity['user_id']}")

    except AWSConnectionError as exc:
        print(f"AWS connection failed: {exc}")


if __name__ == "__main__":
    main()
