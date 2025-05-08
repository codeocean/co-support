import boto3
import requests
import yaml

from botocore.exceptions import ClientError
from typing import Set, Tuple

from co_support.prerequisites.core.prerequisite import Prerequisite


class LinkedRolesCheck(Prerequisite):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            name="Service Linked Roles",
            description=(
                "Checks if the required AWS service-linked roles exist."
            ),
            reference="tinyurl.com/ycyk9fr9",
        )

    def check(self) -> Tuple[bool, str]:
        """
        Verifies the existence of required service-linked roles.
        """
        iam_client = boto3.client("iam")
        existing_roles: Set[str] = set()
        roles_set: Set[str] = set([
            "autoscaling.amazonaws.com",
            "batch.amazonaws.com",
            "ecs.amazonaws.com",
            "elasticfilesystem.amazonaws.com",
            "elasticloadbalancing.amazonaws.com",
            "es.amazonaws.com",
            "rds.amazonaws.com",
            "spot.amazonaws.com",
        ])

        try:
            for role in iam_client.list_roles()["Roles"]:
                if (
                    not role.get("Path", "").startswith("/aws-service-role/")
                    and not role.get("AssumeRolePolicyDocument")
                ):
                    continue

                statements = role[
                    "AssumeRolePolicyDocument"
                ].get("Statement", [])
                for statement in statements:
                    principal = statement.get("Principal", {})
                    service = principal.get("Service", "")
                    existing_roles.add(service)
        except ClientError as e:
            return False, f"Error fetching roles: {e}"

        missing_roles = roles_set - existing_roles
        if missing_roles:
            return False, (
                f"Missing service-linked roles: {', '.join(missing_roles)}."
            )

        return True, "All required service-linked roles exist."


class AdminAccessCheck(Prerequisite):
    def __init__(
        self,
        role_arn: str,
    ) -> None:
        super().__init__(
            name="Administrator Access",
            description=(
                "Checks if the executor role has the "
                "AdministratorAccess policy attached."
            ),
            reference="tinyurl.com/4cp49xmp",
        )
        self.role_arn = role_arn

    def check(self) -> Tuple[bool, str]:
        """
        Determines whether the current user or a given role
        has administrator access.
        """
        iam_client = boto3.client("iam")
        sts_client = boto3.client("sts")

        try:
            if not self.role_arn:
                self.role_arn = sts_client.get_caller_identity()["Arn"]

            role_name = self.role_arn.split("/")[-1]

            if role_name == "CodeOceanLeastPrivilegedDeployRole":
                return True, (
                    "The CodeOceanLeastPrivilegedDeployRole role should have "
                    "the necessary permissions to deploy the "
                    "Code Ocean template."
                )

            if ":assumed-role/" in self.role_arn:
                role_name = self.role_arn.split("/")[-2]

            if ":user/" in self.role_arn:
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
                f"{role_name} does not have the AdministratorAccess policy. "
                "This is acceptable if a least-privileged role is "
                "intentionally being used."
            )

        except ClientError as e:
            return False, f"Error checking admin access: {e}"


class SharedAimiCheck(Prerequisite):
    def __init__(
        self,
        version: str,
        region: str,
        account: str,
    ) -> None:
        super().__init__(
            name="Shared AMI",
            description=(
                "Verifies if the required AMI is shared with "
                "the account in the specified region."
            ),
            reference="tinyurl.com/mrusuenn",
        )
        self.version = version
        self.region = region
        self.account = account

    def check(self) -> Tuple[bool, str]:
        """
        Checks if the AMI is shared with the current account
        in the specified region.
        """
        yaml_url = (
            "https://codeocean-vpc.s3.amazonaws.com/templates/"
            f"{self.version}/codeocean.template.yaml"
        )

        try:
            yaml_content = yaml.safe_load(requests.get(yaml_url, "").text)
            mappings = yaml_content.get("Mappings", {})
            ami_id = mappings.get(
                "AMIs", {},
            ).get(self.region, {}).get("id", "")
            if not ami_id:
                return False, (
                    f"The current region {self.region} is not supported"
                    "in this version"
                )

            ec2_client = boto3.client("ec2")
            try:
                response = ec2_client.describe_images(
                    ImageIds=[ami_id],
                )
                if response.get("Images"):
                    return True, (
                        f"AMI {ami_id} in region {self.region} "
                        f"is shared with account {self.account}"
                    )
            except ClientError as e:
                return False, f"Error checking AMI permissions: {e}"

            return False, (
                f"AMI {ami_id} is not shared with account {self.account}"
            )
        except Exception as e:
            return False, f"Error fetching YAML file: {e}"
