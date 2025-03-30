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

    if not hosting_domain or not hosted_zone_id:
        return SKIP_PREREQ

    domain_parts = hosting_domain.split(".")
    if len(domain_parts) < 3:
        return False, (
            "Invalid domain format. "
            "Expected a subdomain structure (e.g., x.y.z)."
        )

    # Get the parent domain (e.g., y.z)
    parent_domain = ".".join(domain_parts[1:])

    route53_client = boto3.client("route53")

    try:
        response = route53_client.get_hosted_zone(Id=hosted_zone_id)
        subdomain_name_servers = response.get(
            "DelegationSet", {}
        ).get("NameServers", [])

        if not subdomain_name_servers:
            return False, (
                "No name servers found "
                "for the hosted zone delegation set."
            )

        hosted_zones = route53_client.list_hosted_zones()["HostedZones"]
        parent_zone = next(
            (
                zone for zone in hosted_zones
                if zone["Name"].strip(".") == parent_domain
            ),
            None,
        )

        if not parent_zone:
            try:
                resolver = dns.resolver.Resolver()
                answer = resolver.resolve(parent_domain, "NS")
                parent_ns_records = [rdata.to_text() for rdata in answer]

                if not parent_ns_records:
                    return False, (
                        f"Parent domain {parent_domain} "
                        "has no NS records."
                    )

                return True, (
                    f"Parent domain {parent_domain} "
                    "is externally managed."
                )
            except Exception:
                return False, (
                    f"Parent domain {parent_domain} "
                    "does not resolve from any name server."
                )

        parent_zone_id = parent_zone["Id"].split("/")[-1]
        parent_zone_records = route53_client.list_resource_record_sets(
            HostedZoneId=parent_zone_id
        )["ResourceRecordSets"]

        ns_records = [r for r in parent_zone_records if r["Type"] == "NS"]
        if not ns_records:
            return False, (
                f"Parent domain {parent_domain} "
                "is hosted in Route 53 but has no NS records."
            )

        return True, f"Parent domain {parent_domain} is available in Route 53."

    except Exception as e:
        return False, f"Error accessing hosted zone: {str(e)}"


def check_certificate(params: Dict[str, str]) -> Tuple[bool, str]:
    """
    Validates the provided certificate ARN and checks its expiration
    and chain validity.
    """
    cert_arn = params.get("cert_arn")
    is_private_ca = params.get("private_ca", False)

    if not cert_arn:
        return SKIP_PREREQ

    acm = boto3.client("acm")

    try:
        cert_details = acm.describe_certificate(CertificateArn=cert_arn)
        cert_info = cert_details["Certificate"]

        # Expiration check
        expires = cert_info.get("NotAfter")
        if not expires:
            return False, "Certificate expiration date not found."

        days_left = (expires - datetime.now(timezone.utc)).days
        if days_left <= 0:
            return False, "Certificate is expired."

        # Get and verify chain
        cert_chain_response = acm.get_certificate(CertificateArn=cert_arn)
        cert_pem = cert_chain_response.get("Certificate")
        chain_pem = cert_chain_response.get("CertificateChain")

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

            # Choose openssl command
            openssl_cmd = ["openssl", "verify"]
            if not is_private_ca:
                openssl_cmd.append("-partial_chain")
            openssl_cmd += ["-CAfile", chain_path, cert_path]

            result = subprocess.run(
                openssl_cmd, capture_output=True, text=True
            )

            if result.returncode != 0:
                return False, "Certificate chain verification failed."
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
