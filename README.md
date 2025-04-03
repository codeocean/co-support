# Code Ocean Support Command-Line

## Installation

### pip
To install or upgrade the co-support, run the following command:
```bash
pip install --upgrade git+https://github.com/codeocean/co-support.git
```

### virtualenv
To install for development purposes using a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage
```bash
usage: co-support check-prerequisites [-h] [-s | --silent | --no-silent] [-f {table,yaml}] [-o OUTPUT] [--version VERSION] [--role ROLE] [--domain DOMAIN] [--zone HOSTED_ZONE] [--cert CERT]
                                      [--private-ca | --no-private-ca] [--vpc VPC] [--internet-facing | --no-internet-facing]

options:
  -h, --help            show this help message and exit
  -s, --silent, --no-silent
                        Run the script in silent mode (default: False)
  -f, --format {table,yaml}
                        Output format: table or yaml (default: table)
  -o, --output OUTPUT   Path to the directory where the output file will be saved (default: None)
  --version VERSION     Version of Code Ocean to deploy (e.g., v3.4.1) (default: None)
  --role ROLE           ARN of the IAM role to deploy the Code Ocean template (e.g., arn:aws:iam::account-id:role/role-name) (default: None)
  --domain DOMAIN       Domain for the deployment (e.g., codeocean.company.com) (default: None)
  --zone HOSTED_ZONE
                        Hosted zone ID for the deployment (e.g., Z3P5QSUBK4POTI) (default: None)
  --cert CERT           ARN of the SSL/TLS certificate (e.g., arn:aws:acm:region:account:certificate/certificate-id) (default: None)
  --private-ca, --no-private-ca
                        Indicate if the certificate is signed by a private CA (default: False)
  --vpc VPC             ID of the existing VPC (e.g., vpc-0bb1c79de3fd22e7d) (default: None)
  --internet-facing, --no-internet-facing
                        Indicate if the deployment is internet-facing (default: True)
```

### Interactive Example
```bash
co-support check-prerequisites
```

### Silent Example
```bash
co-support check-prerequisites -s \
    --version v3.4.1 \
    --internet-facing \
    --domain codeocean.acmecorp.com \
    --zone A0B1C2D3E4F5G6H7I8J9 \
    --cert arn:aws:acm:us-east-1:000000000000:certificate/01234567-890a-bcde-f012-3456789000 \
    --vpc vpc-0123456789abcdeff \
    --role arn:aws:iam::000000000000:role/Administrator
    --private-ca \
```

## Notes
Currently, this tool only checks prerequisites for Code Ocean deployment.
