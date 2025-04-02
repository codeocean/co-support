import boto3
import requests
import yaml

from botocore.exceptions import ClientError
from typing import Dict, Set, Tuple

from ..core.constants import get_account, get_region


def check_linked_roles(params: Dict[str, Set[str]]) -> Tuple[bool, str]:
    """
    Verifies the existence of required service-linked roles.
    """
    iam_client = boto3.client("iam")
    existing_roles: Set[str] = set()
    roles_set: Set[str] = set(params.get("roles", set()))

    try:
        for role in iam_client.list_roles()["Roles"]:
            if not role.get("Path", "").startswith("/aws-service-role/") and \
               not role.get("AssumeRolePolicyDocument"):
                continue
            statements = role["AssumeRolePolicyDocument"].get("Statement", [])
            for statement in statements:
                principal = statement.get("Principal", {})
                service = principal.get("Service", "")
                existing_roles.add(service)
    except ClientError as e:
        return False, f"Error fetching roles: {e}"

    missing_roles = roles_set - existing_roles
    if not missing_roles:
        return True, "All required service-linked roles exist."

    return False, f"Missing service-linked roles: {', '.join(missing_roles)}."


def check_admin_access(params: Dict[str, str]) -> Tuple[bool, str]:
    """
    Determines whether the current user or a given role
    has administrator access.
    """
    iam_client = boto3.client("iam")
    sts_client = boto3.client("sts")

    try:
        role_arn = params.get("role_arn")
        if not role_arn:
            role_arn = sts_client.get_caller_identity()["Arn"]

        role_name = role_arn.split("/")[-1]
        if ":assumed-role/" in role_arn:
            role_name = role_arn.split("/")[-2]

        if ":user/" in role_arn:
            policies = iam_client.list_attached_user_policies(
                UserName=role_name
            )
        else:
            policies = iam_client.list_attached_role_policies(
                RoleName=role_name
            )

        if any(
            p["PolicyArn"] == "arn:aws:iam::aws:policy/AdministratorAccess"
            for p in policies["AttachedPolicies"]
        ):
            return True, (
                f"{role_name} has AdministratorAccess policy attached."
            )
        return False, (
            f"{role_name} does not have AdministratorAccess policy attached."
        )

    except ClientError as e:
        return False, f"Error checking admin access: {e}"


def check_shared_ami(params: Dict[str, str]) -> Tuple[bool, str]:
    """
    Checks if the AMI is shared with the current account
    in the specified region.
    """
    yaml_url = (
        "https://codeocean-vpc.s3.amazonaws.com/templates/"
        f"{params.get('version', '')}/codeocean.template.yaml"
    )

    try:
        yaml_content = yaml.safe_load(requests.get(yaml_url, "").text)
        mappings = yaml_content.get("Mappings", {})
        ami_id = mappings.get("AMIs", {}).get(get_region(), {}).get("id", "")
        if not ami_id:
            return False, (
                f"The current region {get_region()} "
                "is not supported in this version"
            )

        ec2_client = boto3.client("ec2")
        try:
            response = ec2_client.describe_images(
                ImageIds=[ami_id],
            )
            if response.get("Images"):
                return True, (
                    f"AMI {ami_id} in region {get_region()} "
                    f"is shared with account {get_account()}"
                )
        except ClientError as e:
            return False, f"Error checking AMI permissions: {e}"

        return False, (
            f"AMI {ami_id} is not shared with account {get_account()}"
        )
    except requests.RequestException as e:
        return False, f"Error fetching YAML file: {e}"
