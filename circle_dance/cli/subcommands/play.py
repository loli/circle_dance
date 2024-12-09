import argparse

from circle_dance.cli.subcommands import BaseSubcommand, classproperty
from circle_dance.game import Game, modules


def main():
    print(PlaySubcommand.name)
    args = get_parser().parse_args()
    PlaySubcommand.run(args)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PlaySubcommand.name, description=PlaySubcommand.description)
    PlaySubcommand.add_arguments(parser)
    return parser


class PlaySubcommand(BaseSubcommand):
    "The play subcommand implementation."

    _name = "play"
    _help = "Play a song and visualize the note on a circular music sheet."
    _description = "Play a song and visualize the note on a circular music sheet."

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
        parser.add_argument("filename", help="Song to play.")
        parser.add_argument("-t", "--threshold", type=float, default=0.75, help="Threshold for note detection.")
        parser.add_argument(
            "--note-type", choices=["dot", "arc", "sarc"], default="dot", help="Type of note to use in visualization."
        )

    @staticmethod
    def run(args: argparse.Namespace) -> None:
        g = Game()

        circular_sheet: modules.BaseModule
        if args.note_type == "dot":
            circular_sheet = modules.DotNotesOnCircularSheet(args.filename, threshold=args.threshold)
        elif args.note_type == "sarc":
            circular_sheet = modules.SimpleArcNotesOnCircularSheet(args.filename, threshold=args.threshold)
        else:
            circular_sheet = modules.ArcNotesOnCircularSheet(args.filename, threshold=args.threshold)
        music_player = modules.MusicPlayer(args.filename)

        circular_sheet.register_callbacks(g)
        music_player.register_callbacks(
            g
        )  # note: order can matter; we want music to start after all other setup / pre-run is done

        g.run()


if __name__ == "__main__":
    main()
