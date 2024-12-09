import argparse

from circle_dance.cli.subcommands import BaseSubcommand, classproperty
from circle_dance.game import Game, modules


def main():
    print(ListenSubcommand.name)
    args = get_parser().parse_args()
    ListenSubcommand.run(args)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=ListenSubcommand.name, description=ListenSubcommand.description)
    ListenSubcommand.add_arguments(parser)
    return parser


class ListenSubcommand(BaseSubcommand):
    "The listen subcommand implementation."

    _name = "listen"
    _help = "Listen to the OS's default input device and visualize the note on a circular music sheet."
    _description = "Listen to the OS's default input device and visualize the note on a circular music sheet."

    @classproperty
    def name(cls) -> str:
        return cls._name

    @classproperty
    def help(cls) -> str:
        return cls._help

    @classproperty
    def description(cls) -> str:
        return cls._description

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("-t", "--threshold", type=float, default=0.75, help="Threshold for note detection.")
        parser.add_argument(
            "--note-type", choices=["dot", "arc"], default="dot", help="Type of note to use in visualization."
        )

    @staticmethod
    def run(args: argparse.Namespace) -> None:
        g = Game()

        circular_sheet: modules.BaseModule
        if args.note_type == "dot":
            circular_sheet = modules.DotNotesOnCircularSheetStream(threshold=args.threshold)
        elif args.note_type == "sarc":
            circular_sheet = modules.SimpleArcNotesOnCircularSheetStream(threshold=args.threshold)
        else:
            circular_sheet = modules.ArcNotesOnCircularSheetStream(threshold=args.threshold)
        circular_sheet.register_callbacks(g)

        g.run()


if __name__ == "__main__":
    main()
