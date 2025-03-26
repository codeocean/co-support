from .constants import get_region
from .prerequisite import Prerequisite
from .questions import get_answer, Questions
from .render import print_summary, print_yaml, print_table
from ..checks import access, network, quota, domain


def check_prerequisites(args):
    prerequisites = [
        Prerequisite(
            name="Administrator Access",
            description=(
                "Checks if the executor user has the "
                "AdministratorAccess policy attached."
            ),
            reference="deployment-iam-role",
            function=access.check_admin_access,
        ),
        Prerequisite(
            name="Shared AMI",
            description=(
                "Verifies if the required AMI is shared with "
                "the account in the specified region."
            ),
            reference="prerequisites#request-code-ocean-amis",
            function=access.check_shared_ami,
            parameters={"version": get_answer(Questions.VERSION)},
        ),
        Prerequisite(
            name="DHCP Options",
            description=(
                "Checks that the VPC's DHCP options are set up "
                "to resolve domain names using Amazon DNS."
            ),
            reference="prerequisites#networking",
            function=network.check_dhcp_options,
            parameters={"vpc_id": get_answer(Questions.EXISTING_VPC)},
        ),
        Prerequisite(
            name="Service Linked Roles",
            description=(
                "Checks if the required AWS service-linked roles exist."
            ),
            reference="prerequisites#create-aws-iam-service-linked-roles",
            function=access.check_linked_roles,
            parameters={
                "roles": [
                    "autoscaling.amazonaws.com",
                    "ecs.amazonaws.com",
                    "elasticloadbalancing.amazonaws.com",
                    "es.amazonaws.com",
                    "rds.amazonaws.com",
                    "spot.amazonaws.com",
                    "batch.amazonaws.com",
                    "elasticfilesystem.amazonaws.com",
                ]
            },
        ),
        Prerequisite(
            name="On-Demand Standard Instances",
            description=(
                "Checks if the vCPU quota for On-Demand Standard "
                "instances is sufficient."
            ),
            reference=(
                "prerequisites#running-on-demand-standard"
                "-a-c-d-h-i-m-r-t-z-instances"
            ),
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
            reference="prerequisites#running-on-demand-g-and-vt-instances",
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
                "Checks if there are enough available Elastic IPs and quota."
            ),
            reference="prerequisites#elastic-ips",
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
            reference="prerequisites#networking",
            function=network.check_existing_vpc,
            parameters={"vpc_id": get_answer(Questions.EXISTING_VPC)},
        ),
        Prerequisite(
            name="Hosted Zone",
            description=(
                "Checks if the hosted zone and its parent domain "
                "are correctly configured."
            ),
            reference="prerequisites#choose-a-hosting-domain",
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
            reference="prerequisites#ssl-certificate-validation",
            function=domain.check_certificate,
            parameters={
                "cert_arn": get_answer(Questions.CERT_VALIDATION),
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
        if result == "":
            continue
        data.append([passed, p.name, p.description, result, p.reference])
        if not passed:
            total_failed += 1

    if args.format == "table":
        results = print_table(titles, data)
    elif args.format == "yaml":
        results = print_yaml(titles, data)
    else:
        raise ValueError(f"Unsupported format: {args.format}")

    if args.output:
        path = f"{args.output}/results.{args.format}"
        with open(path, "w") as f:
            f.write(str(results))
        print(f"Results have been written to {path}.")
    else:
        print(results)

    print_summary(total_failed)
