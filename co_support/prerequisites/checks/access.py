import boto3
import requests
import yaml

from typing import Dict, Tuple, Set
from botocore.exceptions import ClientError

from ..core.constants import get_account, get_region


def check_linked_roles(params: Dict) -> Tuple[bool, str]:
    iam_client = boto3.client("iam")
    existing_roles: Set[str] = set()
    roles_set: Set[str] = set(params.get("roles"))

    for role in iam_client.list_roles()["Roles"]:
        if not role.get("Path", "").startswith("/aws-service-role/") and \
           not role.get("AssumeRolePolicyDocument"):
            continue
        statements = role["AssumeRolePolicyDocument"].get("Statement", [])
        for statement in statements:
            principal = statement.get("Principal", {})
            service = principal.get("Service", "")
            existing_roles.add(service)

    missing_roles = roles_set - existing_roles
    if not missing_roles:
        return True, "All required service-linked roles exist."

    return False, f"Missing service-linked roles: {', '.join(missing_roles)}."


def check_admin_access(params: Dict) -> Tuple[bool, str]:
    iam_client = boto3.client("iam")
    sts_client = boto3.client("sts")

    caller_identity = sts_client.get_caller_identity()
    user_arn = caller_identity["Arn"]

    if ":assumed-role/" in user_arn:
        role_name = user_arn.split("/")[-2]
    else:
        user_name = user_arn.split("/")[-1]
        attached_roles = iam_client.list_attached_user_policies(
            UserName=user_name
        )["AttachedPolicies"]
        if any(
            policy["PolicyName"] == "AdministratorAccess"
            for policy in attached_roles
        ):
            return True, "User has AdministratorAccess policy attached."

        return False, "User does not have AdministratorAccess policy attached."

    attached_policies = iam_client.list_attached_role_policies(
        RoleName=role_name
    )["AttachedPolicies"]
    if any(
        policy["PolicyName"] == "AdministratorAccess"
        for policy in attached_policies
    ):
        return True, "Role has AdministratorAccess policy attached."

    return False, "Role does not have AdministratorAccess policy attached."


def check_shared_ami(params: Dict) -> Tuple[bool, str]:
    yaml_url = (
        "https://codeocean-vpc.s3.amazonaws.com/templates/"
        f"{params.get('version')}/codeocean.template.yaml"
    )
    yaml_content = yaml.safe_load(requests.get(yaml_url).text)
    mappings = yaml_content.get('Mappings', {})
    ami_id = mappings.get('AMIs', {}).get(get_region(), {}).get('id')
    if not ami_id:
        return False, (
            f"The current region {get_region()} "
            "is not supported in this version"
        )

    ec2_client = boto3.client('ec2')
    try:
        response = ec2_client.describe_images(
            ImageIds=[ami_id]
        )
        if response.get("Images"):
            return True, (
                f"AMI {ami_id} in region {get_region()} "
                f"is shared with account {get_account()}"
            )
    except ClientError as e:
        return False, f"Error checking AMI permissions: {e}"

    return False, f"AMI {ami_id} is NOT shared with account {get_account()}"
