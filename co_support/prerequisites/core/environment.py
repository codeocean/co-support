import boto3


class Environment:
    """
    This class is used to get the environment information for
    the current AWS session.
    """
    def __init__(
        self,
    ) -> None:
        self.variables = {
            "region": boto3.session.Session().region_name,
            "account": boto3.client("sts").get_caller_identity()["Account"],
            "role": boto3.client("sts").get_caller_identity()["Arn"],
        }
