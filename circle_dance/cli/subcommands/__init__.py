# CLI subcommands
# All subcommands are scripts in their own right, but usually only accessed through the main entrypoint
# A subcommand mostly defines a game via the base game in connection with a selection of game modules

from circle_dance.cli.subcommands.base import BaseSubcommand, classproperty
from circle_dance.cli.subcommands.listen import ListenSubcommand
from circle_dance.cli.subcommands.play import PlaySubcommand

__all__ = ["BaseSubcommand", "classproperty", "PlaySubcommand", "ListenSubcommand"]
