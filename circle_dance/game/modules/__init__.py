# collection of game modules
# each game module adds a functionality to the game
# modules are the objects that stitch together all other elements, such as audio readers, processing, and visualization

from circle_dance.game.modules.base import BaseModule
from circle_dance.game.modules.circular_sheet_file import (
    ArcNotesOnCircularSheet,
    DotNotesOnCircularSheet,
    SimpleArcNotesOnCircularSheet,
)
from circle_dance.game.modules.circular_sheet_stream import (
    ArcNotesOnCircularSheetStream,
    CircularSheetStream,
    DotNotesOnCircularSheetStream,
    SimpleArcNotesOnCircularSheetStream,
)
from circle_dance.game.modules.music_player import MusicPlayer

__all__ = [
    "BaseModule",
    "DotNotesOnCircularSheet",
    "ArcNotesOnCircularSheet",
    "SimpleArcNotesOnCircularSheet",
    "CircularSheetStream",
    "DotNotesOnCircularSheetStream",
    "ArcNotesOnCircularSheetStream",
    "SimpleArcNotesOnCircularSheetStream",
    "MusicPlayer",
]
