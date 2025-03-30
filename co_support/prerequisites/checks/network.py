from typing import Dict, Tuple

import boto3

from ..core.constants import SKIP_PREREQ


def check_existing_vpc(params: Dict[str, str]) -> Tuple[bool, str]:
    """
    Checks if the specified VPC exists and meets the required subnet
    and internet access configurations.
    """
    vpc_id = params.get("vpc_id", "")

    if not vpc_id:
        return SKIP_PREREQ

    ec2_client = boto3.client("ec2")

    try:
        vpc_response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    except Exception as e:
        return False, f"Error describing VPCs: {str(e)}"

    if not vpc_response["Vpcs"]:
        return False, f"VPC with ID {vpc_id} not found."

    try:
        subnets_response = ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
    except Exception as e:
        return False, f"Error describing subnets: {str(e)}"

    subnets = subnets_response["Subnets"]

    private_subnets = [
        subnet for subnet in subnets if subnet["MapPublicIpOnLaunch"] is False
    ]
    public_subnets = [
        subnet for subnet in subnets if subnet["MapPublicIpOnLaunch"] is True
    ]

    subnets_to_check = private_subnets

    if len(private_subnets) < 2:
        return False, (
            "VPC must have at least 2 private subnets. "
            f"Found: {len(private_subnets)}."
        )

    if params.get("internet_facing", ""):
        if len(public_subnets) < 2:
            return False, (
                "VPC must have at least 2 public subnets for "
                f"internet-facing deployment. Found: {len(public_subnets)}."
            )
        subnets_to_check += public_subnets

    for subnet in subnets_to_check:
        cidr_block = subnet["CidrBlock"]
        cidr_block_range = int(cidr_block.split("/")[1])
        if cidr_block_range > 24:
            return False, (
                f"Subnet {subnet['SubnetId']} does not have at least "
                "256 addresses in its CIDR. Found: {cidr_block}"
            )

    try:
        route_table_response = ec2_client.describe_route_tables(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
    except Exception as e:
        return False, f"Error describing route tables: {str(e)}"

    route_tables = route_table_response.get("RouteTables", [])

    subnet_route_table_map = {}
    main_route_table = None

    for rt in route_tables:
        for assoc in rt.get("Associations", []):
            if assoc.get("SubnetId"):
                subnet_route_table_map[assoc["SubnetId"]] = rt
            elif assoc.get("Main"):
                main_route_table = rt

    internet_accessible_subnets = []
    route_misconfigurations = []

    def _has_valid_internet_route(rt: dict) -> bool:
        """Checks if a route table contains a valid default route."""
        for route in rt.get("Routes", []):
            if route.get("DestinationCidrBlock") == "0.0.0.0/0":
                if route.get("GatewayId", "").startswith("igw-"):
                    return True
        return False

    for subnet in public_subnets:
        subnet_id = subnet["SubnetId"]
        route_table = subnet_route_table_map.get(subnet_id, main_route_table)

        if not route_table:
            route_misconfigurations.append(
                f"Subnet {subnet_id} has no associated route table."
            )
            continue

        if _has_valid_internet_route(route_table):
            internet_accessible_subnets.append(subnet_id)
        else:
            route_misconfigurations.append(
                f"Subnet {subnet_id} does not have a valid IGW route."
            )

    if len(internet_accessible_subnets) < 2:
        return False, (
            "Less than 2 public subnets have proper internet access. "
            f"Accessible: {', '.join(internet_accessible_subnets)}. "
            f"Errors: {', '.join(route_misconfigurations)}"
        )

    return True, (
        "VPC has the required subnets and the correct internet "
        "access configurations. Private Subnets: "
        f"{len(private_subnets)}, Public Subnets: {len(public_subnets)}"
    )


def check_dhcp_options(params: Dict[str, str]) -> Tuple[bool, str]:
    """
    Checks if the DHCP options set for the VPC is correctly configured.
    """
    ec2_client = boto3.client("ec2")

    try:
        vpcs = ec2_client.describe_vpcs()["Vpcs"]
    except Exception as e:
        return False, f"Error describing VPCs: {str(e)}"

    existing_vpc = params.get("vpc_id")

    if existing_vpc:
        vpc = next(
            (vpc for vpc in vpcs if vpc.get("VpcId") == existing_vpc), None
        )
    else:
        vpc = next((vpc for vpc in vpcs if vpc.get("IsDefault")), None)

    if not vpc:
        return True, (
            "Test skipped due to not found a default VPC for this account"
        )

    dhcp_option_id = vpc["DhcpOptionsId"]

    try:
        dhcp_options = ec2_client.describe_dhcp_options(
            DhcpOptionsIds=[dhcp_option_id]
        )["DhcpOptions"]
    except Exception as e:
        return False, f"Error describing DHCP options: {str(e)}"

    for option in dhcp_options:
        for config in option["DhcpConfigurations"]:
            if config["Key"] == "domain-name-servers":
                dns_servers = [value["Value"] for value in config["Values"]]

                if ("AmazonProvidedDNS" in dns_servers or
                        "169.254.169.253" in dns_servers):
                    return True, (
                        f"Default DHCP option set ({dhcp_option_id}) is "
                        "correctly configured"
                    )
                else:
                    return False, (
                        f"Default DHCP option set ({dhcp_option_id}) is "
                        "missing 'AmazonProvidedDNS'. Found: {dns_servers}"
                    )

    return False, (
        "No 'domain-name-servers' configuration found in the DHCP option set"
    )
