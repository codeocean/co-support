from co_support.prerequisites.core.prerequisite import (
    Prerequisite,
    SKIP_PREREQ
)
from co_support.prerequisites.core.render import (
    print_summary,
    print_yaml,
    print_table,
)
from co_support.prerequisites.checks import (
    access,
    network,
    quota,
    domain,
)


def check_prerequisites(answers, args):
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
                "role_arn": answers.retrieve("role"),
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
            parameters={
                "version": answers.retrieve("version"),
                "region": args.env["region"],
                "account": args.env["account"],
            },
        ),
        Prerequisite(
            name="DHCP Options",
            description=(
                "Checks that the VPC's DHCP options are set up "
                "to resolve domain names using Amazon DNS."
            ),
            reference="tinyurl.com/yzxf4yv2",
            function=network.check_dhcp_options,
            parameters={"vpc_id": answers.retrieve("existing_vpc")},
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
                "region": args.env["region"],
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
                "region": args.env["region"],
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
                "internet_facing": answers.retrieve("internet_facing"),
                "region": args.env["region"],
                "required_eips": 2,
            },
        ),
        Prerequisite(
            name="Compute Environments",
            description=(
                "Checks if the required Compute Environments (CEs) "
                "is sufficient."
            ),
            reference="tinyurl.com/3hbyk5m5",
            function=quota.check_available_ces,
            parameters={
                "region": args.env["region"],
                "required_ces": 5,
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
                "vpc_id": answers.retrieve("vpc"),
                "internet_facing": answers.retrieve("internet_facing"),
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
                "hosting_domain": answers.retrieve("domain"),
                "hosted_zone_id": answers.retrieve("zone"),
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
                "cert_arn": answers.retrieve("cert"),
                "hosting_domain": answers.retrieve("domain"),
                "private_ca": answers.retrieve("private_ca"),
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
