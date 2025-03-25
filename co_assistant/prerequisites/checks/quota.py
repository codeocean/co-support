import boto3

from typing import Dict, Tuple

from ..core.constants import SKIP_PREREQ, get_region


def check_vcpu_quota(params: Dict) -> Tuple[bool, str]:
    required_vcpus = params.get("required_vcpus")
    service_code = params.get("service_code", "ec2")
    quota_code = params.get("quota_code")

    service_quotas = boto3.client("service-quotas", region_name=get_region())
    ec2_client = boto3.client("ec2", region_name=get_region())

    try:
        quota_response = service_quotas.get_service_quota(
            ServiceCode=service_code,
            QuotaCode=quota_code
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
                    "Values": ["pending", "running"]
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

        if available_vcpus >= required_vcpus:
            return True, (
                f"{available_vcpus} vCPUs available out of {vcpu_limit}."
            )
        else:
            return False, (
                f"Only {available_vcpus} vCPUs available out of "
                f"{vcpu_limit}, but {required_vcpus} required."
            )

    except Exception as e:
        return False, f"Error calculating used vCPUs: {str(e)}"


def check_available_eips(params: Dict) -> Tuple[bool, str]:
    if not params.get("internet_facing"):
        return SKIP_PREREQ

    required_eips = params.get("required_eips")

    ec2_client = boto3.client("ec2", region_name=get_region())
    sq_client = boto3.client("service-quotas", region_name=get_region())

    try:
        eips_response = ec2_client.describe_addresses()
        addresses = eips_response.get("Addresses", [])
        available_eips = [
            eip for eip in addresses if "AssociationId" not in eip
        ]
        available_count = len(available_eips)
        total_allocated = len(addresses)
        quota_response = sq_client.get_service_quota(
            ServiceCode="ec2",
            QuotaCode="L-0263D0A3"
        )
        quota_limit = int(quota_response["Quota"]["Value"])
        remaining_quota = quota_limit - total_allocated
        if remaining_quota < required_eips:
            return False, (
                f"EIP quota exceeded in {get_region()}: {total_allocated}/"
                f"{quota_limit} used, {required_eips} required."
            )

        return True, (
            f"{available_count} available Elastic IP(s), "
            f"{remaining_quota} remaining in quota."
        )

    except Exception as e:
        return False, f"Error checking Elastic IPs or quota: {str(e)}"
