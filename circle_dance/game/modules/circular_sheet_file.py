import librosa

from circle_dance.audio.process import extract_note_durations, extract_note_onsets
from circle_dance.game import Game
from circle_dance.game.modules import BaseModule
from circle_dance.visualize import circular_sheet


class CircularSheet(BaseModule):
    "Base class for all notes on a circular sheet parsed from a file."

    def __init__(self, fn: str, threshold: float = 0.75, n_clones: int = 1):
        """Module that parses an audio file and animate it's notes on a circular sheet.

        Best combined with the `MusicPlayer` module to play the audio while the notes are animated

        Args:
            fn: the song file
            threshold: the chroma energy threshold for considering a note as active; between 0 and 1
            n_clones: number of times to clone the song to produce multiple sheets in the visualization
        """
        assert threshold > 0 and threshold <= 1, "threshold must be between 0 and 1"
        assert n_clones > 0, "n_clones must be greater than 0"

        self.fn = fn
        self.threshold = threshold
        self.n_clones = n_clones

        self.canvas: circular_sheet.Canvas

    def _teardown(self, g: Game):
        pass

    def _pre_run(self, g: Game, clock: float):
        pass

    def _post_run(self, g: Game, clock: float):
        pass

    def _update(self, g: Game, clock: float):
        "Draw the complete scene onto the screen."
        self.canvas.draw(clock)

    def _should_terminate(self, g: Game, clock: float) -> bool:
        "Will never request the game to terminate."
        return False

    def _load_audio(self):
        # load song data
        y, sr = librosa.load(self.fn, sr=None)  # sr = None means using native sampling rate
        ys = [y] * self.n_clones  # fake multi-stem data by cloning
        return ys, sr


class DotNotesOnCircularSheet(CircularSheet):

    def _setup(self, g: Game):
        """Parse audio and setup the visualization and note pool."""
        ys, sr = self._load_audio()

        # Init canvas
        self.canvas = circular_sheet.Canvas(g.screen, len(ys), circular_sheet.DotNotePool)

        # Extract note onsets
        for i in range(len(ys)):
            note_onsets = extract_note_onsets(ys[i], sr, threshold=self.threshold)
            for note, onset, conclusion, energy in note_onsets:
                self.canvas.add_note(i, int(note), onset, conclusion, energy)


class SimpleArcNotesOnCircularSheet(CircularSheet):
    def _setup(self, g: Game):
        """Parse audio and setup the visualization and note pool."""
        ys, sr = self._load_audio()

        # Init canvas
        self.canvas = circular_sheet.Canvas(g.screen, len(ys), circular_sheet.SimpleArcNotePool)

        # Extract note onsets
        for i in range(len(ys)):
            note_onsets = extract_note_durations(ys[i], sr, thr=self.threshold)
            for note, onset, conclusion, energy in note_onsets:
                self.canvas.add_note(i, int(note), onset, conclusion, energy)


class ArcNotesOnCircularSheet(CircularSheet):
    def _setup(self, g: Game):
        """Parse audio and setup the visualization and note pool."""
        ys, sr = self._load_audio()

        # Init canvas
        self.canvas = circular_sheet.Canvas(g.screen, len(ys), circular_sheet.ArcNotePool)

        # Extract note onsets
        for i in range(len(ys)):
            note_onsets = extract_note_durations(ys[i], sr, thr=self.threshold)
            for note, onset, conclusion, energy in note_onsets:
                self.canvas.add_note(i, int(note), onset, conclusion, energy)
