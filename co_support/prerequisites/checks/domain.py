import os
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Tuple

import boto3
import dns.resolver

from co_support.prerequisites.core.prerequisite import (
    SKIP_PREREQ,
    Prerequisite
)


class HostedZoneCheck(Prerequisite):
    def __init__(
        self,
        hosting_domain: str,
        hosted_zone_id: str,
        internet_facing: bool,
    ) -> None:
        super().__init__(
            name="Hosted Zone",
            description=(
                "Checks if the hosted zone and its parent domain "
                 "are correctly configured."
            ),
            reference="tinyurl.com/vsnm7avd",
        )
        self.hosting_domain = hosting_domain
        self.hosted_zone_id = hosted_zone_id
        self.internet_facing = internet_facing

    def check(self) -> Tuple[bool, str]:
        """
        Checks if the provided hosted zone and domain are valid
        and properly configured.
        """
        if not self.hosting_domain or not self.hosted_zone_id:
            return SKIP_PREREQ

        domain_parts = self.hosting_domain.split(".")
        second_level_domain = ".".join(domain_parts[1:])

        if len(domain_parts) < 3:
            return False, (
                "Invalid domain format. "
                "Expected a subdomain structure (e.g., codeocean.company.com)."
            )

        route53_client = boto3.client("route53")

        try:
            zone_details = route53_client.get_hosted_zone(
                Id=self.hosted_zone_id
            )
            zone_name = zone_details.get(
                "HostedZone",
                {}
            ).get("Name", "").strip(".")

            if zone_name not in [self.hosting_domain, second_level_domain]:
                return False, (
                    f"The hosted zone name {zone_name} does not match "
                    f"the provided domain {self.hosting_domain} "
                    "or its parent domain."
                )

            is_private_zone = zone_details.get(
                "Config",
                {},
            ).get("PrivateZone", False)

            if is_private_zone:
                if self.internet_facing:
                    return False, (
                        "The specified hosted zone is private. A public hosted"
                        " zone is required for an internet-facing deployment."
                    )

                return True, (
                    f"The private hosted zone {self.hosted_zone_id} "
                    "is correctly associated with the provided domain."
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
                    f"Delegation is not configured correctly. The NS "
                    f"record for the domain {zone_name} is not resolvable."
                )
            zone_name_servers = zone_details.get(
                "DelegationSet",
                {},
            ).get("NameServers", [])

            if set(resolved_name_servers) != set(zone_name_servers):
                return False, (
                    f"Domain {zone_name} name servers do not match "
                    f"the NS record of the hosted zone {self.hosted_zone_id}."
                )
        except Exception as e:
            return False, f"Error while resolving NS records: {str(e)}"

        try:
            record_sets = route53_client.list_resource_record_sets(
                HostedZoneId=self.hosted_zone_id
            )
            a_records = set([
                record["Name"] for record in record_sets.get(
                    "ResourceRecordSets",
                    [],
                )
                if record.get("Type") == "A"
            ])

            records_to_check = set([
                f"{self.hosting_domain}.",
                f"registry.{self.hosting_domain}.",
                f"analytics.{self.hosting_domain}."
            ])

            if records_to_check & a_records:
                return False, (
                    "One of the Code Ocean A records was found in the hosted "
                    "zone. These records should not be present and are "
                    "expected to be created during the deployment process."
                )
        except Exception as e:
            return False, f"Error while checking A records: {str(e)}"

        return True, (
            "Hosted zone is valid and properly configured."
        )


class CertificateCheck(Prerequisite):
    def __init__(
        self,
        cert_arn: str,
        hosting_domain: str,
        private_ca: bool,
    ) -> None:
        super().__init__(
            name="Certificate",
            description=(
                "Validates the SSL/TLS certificate and its chain of trust."
            ),
            reference="tinyurl.com/bdfp2a4s",
        )
        self.cert_arn = cert_arn
        self.hosting_domain = hosting_domain
        self.private_ca = private_ca

    def check(self) -> Tuple[bool, str]:
        """
        Validates the provided certificate ARN and checks its expiration
        and chain validity.
        """
        if not self.cert_arn or not self.hosting_domain:
            return SKIP_PREREQ

        acm = boto3.client("acm")

        try:
            cert_details = acm.describe_certificate(
                CertificateArn=self.cert_arn
            )
            subject_alternative_names = set(cert_details["Certificate"].get(
                "SubjectAlternativeNames",
                [],
            ))
            required_names = set([
                self.hosting_domain,
                f"*.{self.hosting_domain}"
            ])
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

            cert = acm.get_certificate(CertificateArn=self.cert_arn)
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
                if not self.private_ca:
                    openssl_cmd.append("-partial_chain")
                openssl_cmd += ["-CAfile", chain_path, cert_path]

                result = subprocess.run(
                    openssl_cmd, capture_output=True, text=True
                )

                if result.returncode != 0:
                    return False, "Certificate verification failed."
            elif not self.private_ca:
                return False, (
                    "Missing certificate chain for "
                    "public certificate."
                )

            return True, "Certificate is valid."

        except Exception as e:
            return False, f"Error while checking certificate: {str(e)}"

        finally:
            if "cert_path" in locals() and os.path.exists(cert_path):
                os.remove(cert_path)
            if "chain_path" in locals() and os.path.exists(chain_path):
                os.remove(chain_path)
