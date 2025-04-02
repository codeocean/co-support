from .constants import get_region, SKIP_PREREQ
from .prerequisite import Prerequisite
from .questions import get_answer, Questions
from .render import print_summary, print_yaml, print_table
from ..checks import access, network, quota, domain


def check_prerequisites(args):
    prerequisites = [
        Prerequisite(
            name="Administrator Access",
            description=(
                "Checks if the executor role has the "
                "AdministratorAccess policy attached."
            ),
            reference="tinyurl.com/4cp49xmp",
            function=access.check_admin_access,
            parameters={
                "role_arn": get_answer(Questions.ROLE_ARN),
            }
        ),
        Prerequisite(
            name="Shared AMI",
            description=(
                "Verifies if the required AMI is shared with "
                "the account in the specified region."
            ),
            reference="tinyurl.com/mrusuenn",
            function=access.check_shared_ami,
            parameters={"version": get_answer(Questions.VERSION)},
        ),
        Prerequisite(
            name="DHCP Options",
            description=(
                "Checks that the VPC's DHCP options are set up "
                "to resolve domain names using Amazon DNS."
            ),
            reference="tinyurl.com/yzxf4yv2",
            function=network.check_dhcp_options,
            parameters={"vpc_id": get_answer(Questions.EXISTING_VPC)},
        ),
        Prerequisite(
            name="Service Linked Roles",
            description=(
                "Checks if the required AWS service-linked roles exist."
            ),
            reference="tinyurl.com/ycyk9fr9",
            function=access.check_linked_roles,
            parameters={
                "roles": [
                    "autoscaling.amazonaws.com",
                    "batch.amazonaws.com",
                    "ecs.amazonaws.com",
                    "elasticfilesystem.amazonaws.com",
                    "elasticloadbalancing.amazonaws.com",
                    "es.amazonaws.com",
                    "rds.amazonaws.com",
                    "spot.amazonaws.com",
                ]
            },
        ),
        Prerequisite(
            name="On-Demand Standard Instances",
            description=(
                "Checks if the vCPU quota for On-Demand Standard "
                "instances is sufficient."
            ),
            reference="tinyurl.com/mwz5s3th",
            function=quota.check_vcpu_quota,
            parameters={
                "quota_code": "L-1216C47A",
                "service_code": "ec2",
                "required_vcpus": 34,
                "region": get_region(),
            },
        ),
        Prerequisite(
            name="On-Demand G and VT Instances",
            description=(
                "Checks if the vCPU quota for On-Demand G and VT "
                "instances is sufficient."
            ),
            reference="tinyurl.com/3c2pvau2",
            function=quota.check_vcpu_quota,
            parameters={
                "quota_code": "L-DB2E81BA",
                "service_code": "ec2",
                "required_vcpus": 32,
                "region": get_region(),
            },
        ),
        Prerequisite(
            name="Available EIPs",
            description=(
                "Checks if the addresses quota for Elastic IPs is sufficient."
            ),
            reference="tinyurl.com/2878e6at",
            function=quota.check_available_eips,
            parameters={
                "internet_facing": get_answer(Questions.INTERNET_FACING),
                "required_eips": 2,
            },
        ),
        Prerequisite(
            name="Existing VPC",
            description=(
                "Validates the existing VPC for required subnets and "
                "internet access configurations."
            ),
            reference="tinyurl.com/yzxf4yv2",
            function=network.check_existing_vpc,
            parameters={
                "vpc_id": get_answer(Questions.EXISTING_VPC),
                "internet_facing": get_answer(Questions.INTERNET_FACING),
            },
        ),
        Prerequisite(
            name="Hosted Zone",
            description=(
                "Checks if the hosted zone and its parent domain "
                "are correctly configured."
            ),
            reference="tinyurl.com/vsnm7avd",
            function=domain.check_hosted_zone,
            parameters={
                "hosting_domain": get_answer(Questions.HOSTING_DOMAIN),
                "hosted_zone_id": get_answer(Questions.ROUTE53_EXISTING),
            },
        ),
        Prerequisite(
            name="Certificate",
            description=(
                "Validates the SSL/TLS certificate and its chain of trust."
            ),
            reference="tinyurl.com/bdfp2a4s",
            function=domain.check_certificate,
            parameters={
                "cert_arn": get_answer(Questions.CERT_VALIDATION),
                "hosting_domain": get_answer(Questions.HOSTING_DOMAIN),
                "private_ca": get_answer(Questions.PRIVATE_CA),
            },
        ),
    ]

    print("Starting prerequisite checks...")
    total_failed = 0
    titles = ["Status", "Name", "Description", "Result", "Reference"]
    data = []

    for p in prerequisites:
        passed, result = p.check()
        if (passed, result) == SKIP_PREREQ:
            continue

        data.append([passed, p.name, p.description, result, p.reference])
        if not passed:
            total_failed += 1

    match args.format:
        case "table":
            results = print_table(titles, data)
        case "yaml":
            results = print_yaml(titles, data)
        case _:
            raise ValueError(f"Unsupported format: {args.format}")

    if args.output:
        path = f"{args.output}/results.{args.format}"
        with open(path, "w") as f:
            f.write(str(results))
        print(f"Results have been written to {path}.")
    else:
        print(results)

    print_summary(total_failed)
