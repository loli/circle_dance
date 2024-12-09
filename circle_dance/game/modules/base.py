# base module interface
# only used for convenience, modules don't have to implement this and can register their callbacks otherwise

import abc

from circle_dance.game import Game


class BaseModule(abc.ABC):
    """Convenience module base class.

    Simply subclass and define all the internal callback methods.
    When used, initialize and call `register_callbacks()` on the Game.

    If a callback is not needed, implement it with `pass` as body.
    """

    @abc.abstractmethod
    def _setup(self, g: Game):
        """Setup the module."""
        pass

    @abc.abstractmethod
    def _teardown(self, g: Game):
        """Teardown module."""
        pass

    @abc.abstractmethod
    def _pre_run(self, g: Game, clock: float):
        """Initializations to perform at clock = 0."""
        pass

    @abc.abstractmethod
    def _post_run(self, g: Game, clock: float):
        """Teardowns to perform at last clock tick."""
        pass

    @abc.abstractmethod
    def _update(self, g: Game, clock: float):
        "Perform update of module, potentially depending on clock, during run."
        pass

    @abc.abstractmethod
    def _should_terminate(self, g: Game, clock: float) -> bool:
        """Request game termination."""
        pass

    def register_callbacks(self, g: Game):
        """Register the module's callbacks with the game."""
        g.register_setup_callback(self._setup)
        g.register_teardown_callback(self._teardown)
        g.register_pre_run_callback(self._pre_run)
        g.register_post_run_callback(self._post_run)
        g.register_update_callback(self._update)
        g.register_should_terminate_callback(self._should_terminate)
