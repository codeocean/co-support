from setuptools import setup, find_packages

setup(
    name='co-support',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'argparse',
        'boto3',
        'requests',
        'PyYAML',
        'prettytable',
        'colorama',
        'dnspython',
    ],
    entry_points={
        'console_scripts': [
            'co-support=co_support.main:main',
        ],
    },
)
