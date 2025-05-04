from argparse import _SubParsersAction, BooleanOptionalAction

from co_support.prerequisites.core.questions import Questions
from co_support.prerequisites.core.answers import Answers
from co_support.prerequisites.core.checks import check_prerequisites
from co_support.prerequisites.core.environment import Environment
from co_support.cmd import BaseCommand


def commands(subparsers: _SubParsersAction) -> None:
    """
    Registers all commands for the prerequisites module.
    """
    CheckPrerequisites(subparsers)


class CheckPrerequisites(BaseCommand):
    """
    Command to check prerequisites for Code Ocean deployment.
    """

    def __init__(self, subparsers: _SubParsersAction) -> None:
        super().__init__(subparsers, "check-prerequisites")
        self.parser.add_argument(
            "-s", "--silent",
            help="Run the script in silent mode",
            action=BooleanOptionalAction,
            default=False,
        )
        self.parser.add_argument(
            "-f", "--format",
            choices=["table", "yaml"],
            default="table",
            help="Output format: table or yaml",
        )
        self.parser.add_argument(
            "-o", "--output",
            help="Path to the directory where the output file will be saved",
            default=None,
        )
        self.parser.add_argument(
            "--version",
            help="Version of Code Ocean to deploy (e.g., v3.4.1)",
        )
        self.parser.add_argument(
            "--role",
            help=(
                "ARN of the IAM role to deploy the Code Ocean template "
                "(e.g., arn:aws:iam::account-id:role/role-name)"
            ),
        )
        self.parser.add_argument(
            "--domain",
            help="Domain for the deployment (e.g., codeocean.company.com)",
        )
        self.parser.add_argument(
            "--zone",
            help="Hosted zone ID for the deployment (e.g., Z3P5QSUBK4POTI)",
        )
        self.parser.add_argument(
            "--cert",
            help=(
                "ARN of the SSL/TLS certificate "
                "(e.g., arn:aws:acm:region:account:certificate/certificate-id)"
            ),
        )
        self.parser.add_argument(
            "--private-ca",
            help="Indicate if the certificate is signed by a private CA",
            action=BooleanOptionalAction,
            default=False,
        )
        self.parser.add_argument(
            "--vpc",
            help="ID of the existing VPC (e.g., vpc-0bb1c79de3fd22e7d)",
        )
        self.parser.add_argument(
            "--internet-facing",
            help="Indicate if the deployment is internet-facing",
            action=BooleanOptionalAction,
            default=True,
        )

    def cmd(self, args) -> None:
        """
        Executes the 'check-prerequisites' command.
        """
        try:
            Environment(args)
            questions = Questions()
            args.answers = Answers(questions, args)

            check_prerequisites(args)
        except Exception as e:
            print(f"Error: {e}")
