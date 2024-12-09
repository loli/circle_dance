import pygame

from circle_dance.game import Game
from circle_dance.game.modules import BaseModule


class MusicPlayer(BaseModule):

    def __init__(self, fn: str):
        """Music player module.

        This game module plays a song while the game runs.
        It starts playing at the beginning of the game's clock.
        It signals for game termination once the song has finished playing.

        !TBD:
        - allow for looping (init parameter)
        - allow to disable termination request on finish

        Args:
            fn: the song file
        """
        self.fn = fn

    def _setup(self, g: Game):
        """Setup the music player."""
        pygame.mixer.init()
        pygame.mixer.music.load(self.fn)

    def _teardown(self, g: Game):
        """Teardown the music player."""
        pygame.mixer.stop()
        pygame.mixer.quit()

    def _pre_run(self, g: Game, clock: float):
        """Pre-run the music player."""
        pygame.mixer.music.play()

    def _post_run(self, g: Game, clock: float):
        """Pre-run the music player."""
        pygame.mixer.music.stop()

    def _update(self, g: Game, clock: float):
        pass

    def _should_terminate(self, g: Game, clock: float) -> bool:
        """Check if the game should terminate because the music has finished."""
        return not pygame.mixer.music.get_busy()
