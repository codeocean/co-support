import re

from enum import Enum
from typing import Dict


class Questions(Enum):
    """
    Enum representing the questions for gathering deployment prerequisites.
    """
    VERSION = (
        "Which version of Code Ocean do you intend to deploy (e.g., v3.4.1)?\n"
    )
    INTRODUCTION = (
        "Would you like to answer a few questions? We can proceed without them"
        ", but the results may be incomplete.\n[y/n]:"
    )
    ROLE_ARN = (
        "Will the Code Ocean template be deployed using the current user?"
        "\n[y/n]:"
        "|Please provide the ARN of the IAM role to be used for deployment:\n"
    )
    HOSTING_DOMAIN = (
        "What is your company's desired hosting domain? (Format: "
        "codeocean.[COMPANYNAME].com):\n"
    )
    ROUTE53_EXISTING = (
        "Are you using an existing Route 53 hosted zone in this AWS account?"
        "\n[n/y]:"
        "|Please provide the hosted zone ID:\n"
    )
    CERT_VALIDATION = (
        "Has your SSL/TLS certificate been validated?\n[n/y]:"
        "|Please provide the certificate ARN:\n"
    )
    PRIVATE_CA = (
        "Is this certificate signed by a private CA?\n[n/y]:"
    )
    EXISTING_VPC = (
        "Are you deploying Code Ocean to an existing VPC?\n[n/y]:"
        "|Please provide the VPC ID:\n"
    )
    INTERNET_FACING = (
        "Will your deployment be internet-facing?\n[y/n]:"
    )


def ask_questions(args) -> Dict[str, str]:
    """
    Prompts the user to answer questions interactively
    or uses provided arguments.
    """
    global _answers

    _answers = {}
    _answers[Questions.VERSION.name] = args.version
    _answers[Questions.ROLE_ARN.name] = args.role
    _answers[Questions.HOSTING_DOMAIN.name] = args.domain
    _answers[Questions.ROUTE53_EXISTING.name] = args.zone
    _answers[Questions.CERT_VALIDATION.name] = args.cert
    _answers[Questions.PRIVATE_CA.name] = args.private_ca
    _answers[Questions.EXISTING_VPC.name] = args.vpc
    _answers[Questions.INTERNET_FACING.name] = args.internet_facing

    if args.silent:
        if not args.version:
            raise ValueError("Version must be provided in silent mode.")
        return _answers

    def default_value(question: str) -> str:
        """
        Extracts the default value from a question string.
        """
        matches = re.findall(r"\[([yn])/([yn])\]", question, re.IGNORECASE)
        for match in matches:
            return match[1]

    for question in Questions:
        if _answers.get(question.name):
            continue

        q = question.value.split("|")
        response = ""
        while not response.strip():
            response = input(q[0] + " ").strip()
            if (
                response.lower() == default_value(q[0])
                and len(q) > 1
            ):
                response = input(q[1] + " ").strip()

        _answers[question.name] = response

        if question == Questions.INTRODUCTION and response.lower() == "n":
            break

    return _answers


def get_answer(question: Enum) -> str:
    """
    Retrieves the answer to a specific question.
    """
    global _answers
    if _answers is None:
        raise ValueError("Answers have not been initialized.")

    answer = _answers.get(question.name, "")
    if isinstance(answer, str) and answer.lower() in ["y", "n"]:
        answer = answer.lower() == "y"

    return answer
