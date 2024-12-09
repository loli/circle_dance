# the subcommand interface

import abc
import argparse


class classproperty:
    "Implementation of @classproperty, as the native @classmethod is depreciated in Python 3.11."

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls=None):
        return self.func(cls)


class BaseSubcommand(abc.ABC):
    "Subcommand static interface definition."

    @classproperty
    @abc.abstractmethod
    def name(cls) -> str:
        "Subcommand name"
        pass

    @classproperty
    @abc.abstractmethod
    def help(cls) -> str:
        "Short description of what the subcommand does"
        pass

    @classproperty
    @abc.abstractmethod
    def description(cls) -> str:
        "Long description of what the subcommand does"
        pass

    @staticmethod
    @abc.abstractmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        "Add arguments to the subcommand parser."
        pass

    @staticmethod
    @abc.abstractmethod
    def run(args: argparse.Namespace) -> None:
        "Run the subcommand"
        pass
