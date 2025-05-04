import boto3


class Environment:
    """
    R
    """
    def __init__(
        self,
        args,
    ) -> None:
        args.region = self.get_region()
        args.account = self.get_account()

    def get_region(self) -> str:
        """
        Retrieves the AWS region for the current session.
        """
        return boto3.session.Session().region_name

    def get_account(self) -> str:
        """
        Retrieves the AWS account ID for the current session.
        """
        return boto3.client("sts").get_caller_identity()["Account"]
