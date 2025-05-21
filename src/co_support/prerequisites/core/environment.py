import boto3


class Environment:
    """
    This class is used to get the environment information for
    the current AWS session.
    """
    def __init__(
        self,
    ) -> None:
        self.region = boto3.session.Session().region_name
        self.account = boto3.client("sts").get_caller_identity()["Account"]
        self.role = boto3.client("sts").get_caller_identity()["Arn"]
