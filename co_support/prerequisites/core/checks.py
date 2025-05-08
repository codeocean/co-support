from co_support.prerequisites.core.prerequisite import (
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
        access.AdminAccessCheck(
            role_arn=answers.retrieve("role"),
        ),
        access.SharedAimiCheck(
            version=answers.retrieve("version"),
            region=args.env.region,
            account=args.env.account,
        ),
        access.LinkedRolesCheck(),
        network.DhcpOptionsCheck(
            vpc_id=answers.retrieve("vpc"),
        ),
        network.ExistingVpcCheck(
            vpc_id=answers.retrieve("vpc"),
            internet_facing=answers.retrieve("internet_facing"),
        ),
        quota.OnDemandGandVTInstancesQuotaCheck(
            region=args.env.region,
        ),
        quota.OnDemandGandVTInstancesQuotaCheck(
            region=args.env.region,
        ),
        quota.AvailableEipCheck(
            region=args.env.region,
            internet_facing=answers.retrieve("internet_facing"),
        ),
        quota.AvailableCEsCheck(
            region=args.env.region,
        ),
        domain.HostedZoneCheck(
            hosting_domain=answers.retrieve("domain"),
            hosted_zone_id=answers.retrieve("zone"),
            internet_facing=answers.retrieve("internet_facing"),
        ),
        domain.CertificateCheck(
            cert_arn=answers.retrieve("cert"),
            hosting_domain=answers.retrieve("domain"),
            private_ca=answers.retrieve("private_ca"),
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
