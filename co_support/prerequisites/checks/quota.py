from typing import Tuple

import boto3

from co_support.prerequisites.core.prerequisite import (
    SKIP_PREREQ,
    Prerequisite,
)


class VcpuQuotaCheck(Prerequisite):
    def __init__(
        self,
        name: str,
        description: str,
        reference: str,
        region: str,
        required_vcpus: int,
        quota_code: str,
        service_code: str = "ec2",
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            reference=reference,
        )
        self.region = region
        self.required_vcpus = required_vcpus
        self.quota_code = quota_code
        self.service_code = service_code

    def check(self) -> Tuple[bool, str]:
        """
        Checks if the required vCPUs are available within the quota limits.
        """
        service_quotas = boto3.client(
            "service-quotas",
            region_name=self.region
        )
        ec2_client = boto3.client("ec2", region_name=self.region)

        try:
            quota_response = service_quotas.get_service_quota(
                ServiceCode=self.service_code,
                QuotaCode=self.quota_code,
            )
            vcpu_limit = int(quota_response["Quota"]["Value"])

        except service_quotas.exceptions.NoSuchResourceException:
            return False, "Quota not found."
        except Exception as e:
            return False, f"Error fetching vCPU quota: {str(e)}"

        try:
            used_vcpus = 0
            paginator = ec2_client.get_paginator("describe_instances")
            page_iterator = paginator.paginate(
                Filters=[
                    {
                        "Name": "instance-state-name",
                        "Values": ["pending", "running"],
                    }
                ]
            )

            for page in page_iterator:
                for reservation in page["Reservations"]:
                    for instance in reservation["Instances"]:
                        instance_type = instance["InstanceType"]
                        type_info = ec2_client.describe_instance_types(
                            InstanceTypes=[instance_type]
                        )
                        vcpu_info = type_info["InstanceTypes"][0]["VCpuInfo"]
                        vcpu_count = vcpu_info["DefaultVCpus"]
                        used_vcpus += vcpu_count

            available_vcpus = vcpu_limit - used_vcpus

            if available_vcpus >= self.required_vcpus:
                return True, (
                    f"{available_vcpus} vCPUs are available out of a total "
                    f"quota of {vcpu_limit}, meeting the requirement "
                    f"of {self.required_vcpus}."
                )
            else:
                return False, (
                    f"Only {available_vcpus} vCPUs available out of "
                    f"{vcpu_limit}, but {self.required_vcpus} required."
                )

        except Exception as e:
            return False, f"Error calculating used vCPUs: {str(e)}"


class OnDemandStandardVcpuQuotaCheck(VcpuQuotaCheck):
    def __init__(
        self,
        region: str,
    ) -> None:
        super().__init__(
            name="On-Demand Standard Instances",
            description=(
                "Checks if the vCPU quota for On-Demand Standard "
                "instances is sufficient."
            ),
            reference="tinyurl.com/mwz5s3th",
            region=region,
            required_vcpus=34,
            quota_code="L-1216C47A",
        )


class OnDemandGandVTInstancesQuotaCheck(VcpuQuotaCheck):
    def __init__(
        self,
        region: str,
    ) -> None:
        super().__init__(
            name="On-Demand G and VT Instances",
            description=(
                "Checks if the vCPU quota for On-Demand G and VT "
                "instances is sufficient."
            ),
            reference="tinyurl.com/3c2pvau2",
            region=region,
            required_vcpus=32,
            quota_code="L-DB2E81BA",
        )


class AvailableEipCheck(Prerequisite):
    def __init__(
        self,
        region: str,
        internet_facing: bool
    ) -> None:
        super().__init__(
            name="Available EIPs",
            description=(
                "Checks if the addresses quota for Elastic IPs is sufficient."
            ),
            reference="tinyurl.com/2878e6at",
        )
        self.region = region
        self.internet_facing = internet_facing
        self.required_eips = 2

    def check(self) -> Tuple[bool, str]:
        """
        Checks if the required Elastic IPs (EIPs) are available
        within the quota limits.
        """
        if not self.internet_facing:
            return SKIP_PREREQ

        ec2_client = boto3.client("ec2", region_name=self.region)
        sq_client = boto3.client("service-quotas", region_name=self.region)

        try:
            eips_response = ec2_client.describe_addresses()
            addresses = eips_response.get("Addresses", [])
            total_allocated = len(addresses)
            quota_response = sq_client.get_service_quota(
                ServiceCode="ec2",
                QuotaCode="L-0263D0A3",
            )
            quota_limit = int(quota_response["Quota"]["Value"])
            remaining_quota = quota_limit - total_allocated

            if remaining_quota < self.required_eips:
                return False, (
                    f"EIP quota exceeded in {self.region}: {total_allocated}/"
                    f"{quota_limit} used, {self.required_eips} required."
                )

            return True, (
                f"{remaining_quota} EIPs are available out of a total "
                f"quota of {quota_limit}, meeting the requirement "
                f"of {self.required_eips}."
            )

        except Exception as e:
            return False, f"Error checking Elastic IPs or quota: {str(e)}"


class AvailableCEsCheck(Prerequisite):
    def __init__(
        self,
        region: str,
    ) -> None:
        super().__init__(
            name="Available Compute Environments",
            description=(
                "Checks if the required Compute Environments (CEs) "
                "is sufficient."
            ),
            reference="tinyurl.com/3hbyk5m5",
        )
        self.region = region
        self.required_ces = 5

    def check(self) -> Tuple[bool, str]:
        """
        Checks if the required Compute Environments (CEs) are available
        within the quota limits.
        """
        sq_client = boto3.client("service-quotas", region_name=self.region)

        try:
            quota_response = sq_client.get_service_quota(
                ServiceCode="batch",
                QuotaCode="L-144F0CA5",
            )
            quota_limit = int(quota_response["Quota"]["Value"])

            client = boto3.client('batch', region_name=self.region)
            total_ces = len(
                client.describe_compute_environments().get(
                    "computeEnvironments"
                )
            )

            if quota_limit < self.required_ces + total_ces:
                msg = (
                    f"Quota limit for Compute Environments exceeded in "
                    f"{self.region}: {total_ces} CEs already exist, "
                    f"{self.required_ces} required."
                )

                if quota_limit == 50:
                    msg += (
                        " 50 is the macximum number of CEs allowed per "
                        "region. Please delete some CEs to proceed."
                    )

                return False, (msg)

            return True, (
                f"{quota_limit - total_ces} CEs are available out of a total "
                f"quota of {quota_limit}, meeting the requirement "
                f"of {self.required_ces}."
            )

        except Exception as e:
            return False, (
                "Error checking Compute Environments or quota: "
                f"{str(e)}"
            )
