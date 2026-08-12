from app.collectors.aws.ec2 import (
    EC2CollectorError,
    collect_ec2_instances,
)


def main():
    try:
        instances = collect_ec2_instances()

        print(f"Found {len(instances)} EC2 instances")

        for instance in instances:
            print(instance)

    except EC2CollectorError as exc:
        print(exc)


if __name__ == "__main__":
    main()

