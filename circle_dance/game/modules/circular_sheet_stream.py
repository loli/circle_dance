import logging
import threading
from abc import ABC, abstractmethod
from queue import Empty, Queue

from circle_dance.audio.read import callbacks, stream_reader
from circle_dance.game import Game
from circle_dance.game.modules import BaseModule
from circle_dance.visualize import circular_sheet

logger = logging.getLogger(__name__)


class CircularSheetStream(BaseModule, ABC):
    "Base class for all notes on a circular sheet parsed from a stream."

    def __init__(self, threshold: float = 0.99, n_clones: int = 1):
        """Module that parses the OS's default input stream and animate it's notes on a circular sheet.

        Uses a thread to process the stream for faster processing.

        Args:
            threshold: the energy threshold for considering a note as active; between 0 and 1
            n_clones: number of times to clone the song to produce multiple sheets in the visualization
        """
        assert threshold > 0 and threshold <= 1, "threshold must be between 0 and 1"
        assert n_clones > 0, "n_clones must be greater than 0"

        self.threshold = threshold
        self.n_clones = n_clones  # !TBD: Currently not used. Implement?
        self.thread: threading.Thread
        self.close_request_event: threading.Event
        self.queue: Queue

    @abstractmethod
    def start_subprocess(self):
        "Start the thread that reads the stream and adds notes to the queue."
        pass

    def stop_subprocess(self):
        if self.thread.is_alive():
            self.close_request_event.set()
            self.thread.join(timeout=2)  # maximum time in seconds to wait for subprocess to terminate itself
        #    if self.thread.exitcode is None:
        #        self.thread.terminate()
        # self.thread.close()

    def _setup(self, g: Game):
        self.canvas = circular_sheet.Canvas(g.screen, n_sheets=1, note_pool=circular_sheet.DotNotePool)

    def _teardown(self, g: Game):
        self.stop_subprocess()

    def _pre_run(self, g: Game, clock: float):
        self.start_subprocess()

    def _post_run(self, g: Game, clock: float):
        pass

    def _update(self, g: Game, clock: float):
        note: float
        onset: float
        conclusion: float
        energy: float

        # read all pending notes from the queue and add to canvas
        while not self.queue.empty():
            try:
                note, onset, conclusion, energy = self.queue.get_nowait()
                self.canvas.add_note(0, int(note), onset, conclusion, energy)
            except Empty:
                pass

        # draw canvas
        self.canvas.draw(clock)

    def _should_terminate(self, g: Game, clock: float) -> bool:
        if not self.thread.is_alive():
            logger.warn("notes_producer subprocess died; signaling game to terminate")
            return True
        return False


class DotNotesOnCircularSheetStream(CircularSheetStream):

    def start_subprocess(self):
        self.queue = Queue()  # queue for notes
        self.close_request_event = threading.Event()
        self.thread = threading.Thread(
            target=stream_reader,
            args=(callbacks.extract_node_onsets_callback, self.queue, self.close_request_event, 5, 20),
            # buffer_replenish_multiplier, buffer_carryover_multiplier
        )
        self.thread.start()


class SimpleArcNotesOnCircularSheetStream(CircularSheetStream):

    def start_subprocess(self):
        self.queue = Queue()  # queue for notes
        self.close_request_event = threading.Event()
        self.thread = threading.Thread(
            target=stream_reader,
            args=(callbacks.extract_note_durations_callback, self.queue, self.close_request_event, 1, 20),
            # buffer_replenish_multiplier, buffer_carryover_multiplier
        )
        self.thread.start()

    def _setup(self, g: Game):
        self.canvas = circular_sheet.Canvas(g.screen, n_sheets=1, note_pool=circular_sheet.SimpleArcNotePool)


class ArcNotesOnCircularSheetStream(CircularSheetStream):

    def _setup(self, g: Game):
        self.canvas = circular_sheet.Canvas(g.screen, n_sheets=1, note_pool=circular_sheet.ArcNotePool)
