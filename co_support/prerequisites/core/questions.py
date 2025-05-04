from enum import Enum
from typing import Dict

import re


class QuestionsList(Enum):
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


class Questions:
    """
    Represents the questions for gathering deployment prerequisites.
    """

    def ask(self, skipped_questions) -> Dict[str, str]:
        """
        Prompts the user to answer questions interactively
        or uses provided arguments.
        """
        def default_value(question: str) -> str:
            """
            Extracts the default value from a question string.
            """
            matches = re.findall(r"\[([yn])/([yn])\]", question, re.IGNORECASE)
            for match in matches:
                return match[1]

        user_answers = {}

        for question in QuestionsList:
            if skipped_questions.get(question.name):
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

            user_answers[question.name] = response

            if (
                question == QuestionsList.INTRODUCTION
                and response.lower() == "n"
            ):
                break

        return user_answers
