#!/usr/bin/env python3

import argparse

from .prerequisites.main import commands as prerequisites_commands


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    prerequisites_commands(subparsers)

    return parser.parse_args(), parser


def main():
    args, parser = parse_args()
    if hasattr(args, 'cmd'):
        response = args.cmd(args)
        if response:
            print(response)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
