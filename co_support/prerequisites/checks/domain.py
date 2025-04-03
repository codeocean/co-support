import os
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Dict, Tuple

import boto3
import dns.resolver

from ..core.constants import SKIP_PREREQ


def check_hosted_zone(params: Dict[str, str]) -> Tuple[bool, str]:
    """
    Checks if the provided hosted zone and domain are valid
    and properly configured.
    """
    hosted_zone_id = params.get("hosted_zone_id", "")
    hosting_domain = params.get("hosting_domain", "")
    internet_facing = params.get("internet_facing", False)

    if not hosting_domain or not hosted_zone_id:
        return SKIP_PREREQ

    domain_parts = hosting_domain.split(".")
    second_level_domain = ".".join(domain_parts[1:])

    if len(domain_parts) < 3:
        return False, (
            "Invalid domain format. "
            "Expected a subdomain structure (e.g., codeocean.company.com)."
        )

    route53_client = boto3.client("route53")

    try:
        zone_details = route53_client.get_hosted_zone(Id=hosted_zone_id)
        zone_name = zone_details.get(
            "HostedZone",
            {}
        ).get("Name", "").strip(".")

        if zone_name not in [hosting_domain, second_level_domain]:
            return False, (
                f"The hosted zone name {zone_name} does not match "
                f"the provided domain {hosting_domain} or its parent domain."
            )

        is_private_zone = zone_details.get(
            "Config",
            {},
        ).get("PrivateZone", False)

        if is_private_zone:
            if internet_facing:
                return False, (
                    "The specified hosted zone is private. A public hosted "
                    "zone is required for an internet-facing deployment."
                )

            True, (
                f"The private hosted zone {hosted_zone_id} is correctly "
                "associated with the provided domain."
            )
    except Exception as e:
        return False, f"Error accessing hosted zone: {str(e)}"

    try:
        resolved_ns_record = dns.resolver.resolve(zone_name, "NS")
        resolved_name_servers = [
            name_server.to_text().rstrip('.')
            for name_server in resolved_ns_record
        ]
        if not resolved_name_servers:
            return False, (
                f"Delegation is not configured correctly. "
                f"The NS record for the domain {zone_name} is not resolvable."
            )
        zone_name_servers = zone_details.get(
            "DelegationSet",
            {},
        ).get("NameServers", [])

        if set(resolved_name_servers) != set(zone_name_servers):
            return False, (
                f"Domain {zone_name} name servers do not match "
                f"the NS record of the hosted zone {hosted_zone_id}."
            )
    except Exception as e:
        return False, f"Error while resolving NS records: {str(e)}"

    try:
        record_sets = route53_client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id
        )
        a_records = set([
            record["Name"] for record in record_sets.get("ResourceRecordSets", [])
            if record.get("Type") == "A"
        ])

        records_to_check = set([
            f"{hosting_domain}.",
            f"registry.{hosting_domain}.",
            f"analytics.{hosting_domain}."
        ])

        if records_to_check & a_records:
            return False, (
                "One of the Code Ocean A records was found in the hosted "
                "zone. These records should not be present and are expected "
                "to be created during the deployment process."
            )
    except Exception as e:
        return False, f"Error while checking A records: {str(e)}"

    return True, (
        "Hosted zone is valid and properly configured."
    )


def check_certificate(params: Dict[str, str]) -> Tuple[bool, str]:
    """
    Validates the provided certificate ARN and checks its expiration
    and chain validity.
    """
    cert_arn = params.get("cert_arn")
    is_private_ca = params.get("private_ca", False)
    hosting_domain = params.get("hosting_domain")

    if not cert_arn or not hosting_domain:
        return SKIP_PREREQ

    acm = boto3.client("acm")

    try:
        cert_details = acm.describe_certificate(CertificateArn=cert_arn)
        subject_alternative_names = set(cert_details["Certificate"].get(
            "SubjectAlternativeNames",
            [],
        ))
        required_names = set([hosting_domain, f"*.{hosting_domain}"])
        if not required_names.issubset(subject_alternative_names):
            return False, (
                f"Certificate does not cover the required domains: "
                f"{', '.join(required_names)}."
            )

        expires = cert_details["Certificate"].get("NotAfter")
        if not expires:
            return False, "Certificate expiration date not found."

        days_left = (expires - datetime.now(timezone.utc)).days
        if days_left <= 0:
            return False, "Certificate is expired."

        cert = acm.get_certificate(CertificateArn=cert_arn)
        cert_pem = cert.get("Certificate")
        chain_pem = cert.get("CertificateChain")

        if not cert_pem:
            return False, "Certificate body not found."

        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", suffix=".pem"
        ) as cert_file:
            cert_file.write(cert_pem)
            cert_path = cert_file.name

        if chain_pem:
            with tempfile.NamedTemporaryFile(
                delete=False, mode="w", suffix=".pem"
            ) as chain_file:
                chain_file.write(chain_pem)
                chain_path = chain_file.name

            openssl_cmd = ["openssl", "verify"]
            if not is_private_ca:
                openssl_cmd.append("-partial_chain")
            openssl_cmd += ["-CAfile", chain_path, cert_path]

            result = subprocess.run(
                openssl_cmd, capture_output=True, text=True
            )

            if result.returncode != 0:
                return False, "Certificate verification failed."
        elif not is_private_ca:
            return False, "Missing certificate chain for public certificate."

        return True, "Certificate is valid."

    except Exception as e:
        return False, f"Error while checking certificate: {str(e)}"

    finally:
        if "cert_path" in locals() and os.path.exists(cert_path):
            os.remove(cert_path)
        if "chain_path" in locals() and os.path.exists(chain_path):
            os.remove(chain_path)
