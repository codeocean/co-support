import boto3
from typing import Optional

_region: Optional[str] = None
_account: Optional[str] = None


def get_region() -> str:
    """
    Retrieves the AWS region for the current session.
    """
    global _region
    if _region is None:
        _region = boto3.session.Session().region_name
    return _region


def get_account() -> str:
    """
    Retrieves the AWS account ID for the current session.
    """
    global _account
    if _account is None:
        _account = boto3.client("sts").get_caller_identity()["Account"]
    return _account


SKIP_PREREQ = (True, "")
