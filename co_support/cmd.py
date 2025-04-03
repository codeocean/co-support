from abc import ABC, abstractmethod
from argparse import ArgumentDefaultsHelpFormatter


class BaseCommand(ABC):
    """
    Base class for commands.
    """

    def __init__(self, subparsers, name, format_map=None):
        self.parser = subparsers.add_parser(
            name=name.format_map(format_map),
            help=self.__doc__.strip().format_map(format_map),
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        self.parser.set_defaults(cmd=self.cmd)

    @abstractmethod
    def cmd(args):
        pass
