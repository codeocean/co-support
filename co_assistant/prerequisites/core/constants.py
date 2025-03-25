import boto3

_region = None
_account = None


def get_region():
    global _region
    if _region is None:
        _region = boto3.session.Session().region_name
    return _region


def get_account():
    global _account
    if _account is None:
        _account = boto3.client('sts').get_caller_identity()['Account']
    return _account


SKIP_PREREQ = (True, "")
