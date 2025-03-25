from .core.questions import ask_questions
from .core.checks import run_checks
from ..cmd import BaseCommand


def commands(subparsers):
    """
    Check prerequisites for Code Ocean deployment.
    """
    CheckPrerequisites(subparsers)


class CheckPrerequisites(BaseCommand):
    """
    Check prerequisites for Code Ocean deployment.
    """

    def __init__(self, subparsers):
        super().__init__(subparsers, 'check-prerequisites')
        self.parser.add_argument(
            '-s', '--silent',
            help='Run the script in silent mode',
            action='store_true'
        )
        self.parser.add_argument(
            '-f', '--format',
            choices=['table', 'yaml'],
            default='table',
            help='Output format: table or yaml'
        )
        self.parser.add_argument(
            '-o', '--output',
            help='Output file path',
            default=None
        )
        self.parser.add_argument(
            '--version',
            help='Version of Code Ocean to deploy (e.g., v3.4.1)'
        )
        self.parser.add_argument(
            '--domain',
            help='Domain for the deployment (e.g., codeocean.company.com)'
        )
        self.parser.add_argument(
            '--hosted-zone',
            help='Hosted zone ID for the deployment (e.g., Z3P5QSUBK4POTI)'
        )
        self.parser.add_argument(
            '--cert',
            help=(
                "ARN of the SSL/TLS certificate "
                "(e.g., arn:aws:acm:region:account:certificate/certificate-id)"
            )
        )
        self.parser.add_argument(
            '--private-ca',
            help='Indicate if the certificate is signed by a private CA',
            action='store_true'
        )
        self.parser.add_argument(
            '--vpc',
            help='ID of the existing VPC (e.g., vpc-0bb1c79de3fd22e7d)'
        )
        self.parser.add_argument(
            '--internet-facing',
            help='Indicate if the deployment is internet-facing',
            action='store_true'
        )

    def cmd(self, args):
        ask_questions(args)
        run_checks(args)
