# main CLI entrypoint, actual work is handled by subcommands

import argparse
import logging

from circle_dance.cli import subcommands

logger = logging.getLogger(__name__)


def main():
    args = get_parser().parse_args()

    # handle global arguments
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # call subcommand entrypoint
    args.func(args)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="circle_dance", description="Visualize audio notes on a circular sheet.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")

    subparsers = parser.add_subparsers(description="Choose a functionality.", required=True)  # , metavar="")

    # add subparsers
    __register_subcommand(subparsers, subcommands.PlaySubcommand)
    __register_subcommand(subparsers, subcommands.ListenSubcommand)

    return parser


def __register_subcommand(sps: argparse._SubParsersAction, sc: type[subcommands.BaseSubcommand]):
    sc_parser = sps.add_parser(
        sc.name,
        help=sc.help,
        description=sc.description,
    )
    sc.add_arguments(sc_parser)
    sc_parser.set_defaults(func=sc.run)


if __name__ == "__main__":
    main()
