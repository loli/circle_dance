# principal game runner

import functools
import time
from typing import Callable, TypeAlias

import pygame


class Game:

    # base types
    __T_CALLBACK_WO_CLOCK: TypeAlias = Callable[["Game"], None]  # note: forward reference
    __T_CALLBACK_W_CLOCK: TypeAlias = Callable[["Game", float], None]

    # callback types
    T_CALLBACK_SETUP: TypeAlias = __T_CALLBACK_WO_CLOCK
    T_CALLBACK_TEARDOWN: TypeAlias = __T_CALLBACK_WO_CLOCK
    T_CALLBACK_PRE_RUN: TypeAlias = __T_CALLBACK_W_CLOCK
    T_CALLBACK_POST_RUN: TypeAlias = __T_CALLBACK_W_CLOCK
    T_CALLBACK_UPDATE: TypeAlias = __T_CALLBACK_W_CLOCK
    T_CALLBACK_SHOULD_TERMINATE: TypeAlias = Callable[["Game", float], bool]
    T_CALLBACK_KEYDOWN: TypeAlias = __T_CALLBACK_WO_CLOCK

    def __init__(self) -> None:
        """Game implementation.

        Takes care of initializing pygame, prepares the screen, maintains the synchronization clock, and provides a
        callback interface for modules to register to.

        Also takes care of teardown and all global functionality, such as processing quit commands.

        !TBD:
            - add some parameters (e.g. fullscreen, window size, window title)
            - add some logging
            - add some way to register event callbacks (e.g. key press, mouse click)
            - add some error handling (quit game gracefully)
            - callbacks registration also need to provide module name for better debug logging
            - print debug info on click duration, e.g. every 10 clicks the average or such
        """
        self.__callbacks_setup: list[Game.T_CALLBACK_SETUP] = []
        self.__callbacks_teardown: list[Game.T_CALLBACK_TEARDOWN] = []
        self.__callbacks_pre_run: list[Game.T_CALLBACK_PRE_RUN] = []
        self.__callbacks_post_run: list[Game.T_CALLBACK_POST_RUN] = []
        self.__callbacks_update: list[Game.T_CALLBACK_UPDATE] = []
        self.__callbacks_should_terminate: list[Game.T_CALLBACK_SHOULD_TERMINATE] = []
        self.__callbacks_keydown: dict[int, Game.T_CALLBACK_KEYDOWN] = {}

    def run(self) -> None:
        "Run the game."
        # setup
        self._setup()
        [c(self) for c in self.__callbacks_setup]

        # Animation loop
        start_time = time.time()
        clock = 0.0
        running = True

        # pre-run callbacks
        [c(self, clock) for c in self.__callbacks_pre_run]

        while running:
            # exit on ESC and pygame.QUIT
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in self.__callbacks_keydown:
                    self.__callbacks_keydown[event.key](self)  # handle keydown callbacks

            # update clock
            clock = time.time() - start_time

            # update by calling update on each module
            # mainly used to update the screen
            [c(self, clock) for c in self.__callbacks_update]

            pygame.display.flip()

            # check if termination desire signaled by any module
            if functools.reduce(lambda a, b: a or b, [c(self, clock) for c in self.__callbacks_should_terminate]):
                running = False

        # post-run callbacks
        clock = time.time() - start_time
        [c(self, clock) for c in self.__callbacks_post_run]

        # teardown
        [c(self) for c in self.__callbacks_teardown]
        self._teardown()

    def register_setup_callback(self, callback: T_CALLBACK_SETUP) -> None:
        self.__callbacks_setup.append(callback)

    def register_teardown_callback(self, callback: T_CALLBACK_TEARDOWN) -> None:
        self.__callbacks_teardown.append(callback)

    def register_pre_run_callback(self, callback: T_CALLBACK_PRE_RUN) -> None:
        self.__callbacks_pre_run.append(callback)

    def register_post_run_callback(self, callback: T_CALLBACK_POST_RUN) -> None:
        self.__callbacks_post_run.append(callback)

    def register_update_callback(self, callback: T_CALLBACK_UPDATE) -> None:
        self.__callbacks_update.append(callback)

    def register_should_terminate_callback(self, callback: T_CALLBACK_SHOULD_TERMINATE) -> None:
        self.__callbacks_should_terminate.append(callback)

    def register_keydown_callback(self, key: int, callback: T_CALLBACK_KEYDOWN) -> None:
        self.__callbacks_keydown[key] = callback

    def _setup(self) -> None:
        "Game setup, before the clock starts."
        pygame.init()

        # get screen resolution
        info = pygame.display.Info()
        screen_width, screen_height = info.current_w, info.current_h

        # Screen setup
        width, height = screen_width, screen_height
        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
        pygame.display.set_caption("Circular Music Sheet Animation")

        self.screen = screen

    def _teardown(self) -> None:
        "Game teardown, after the clock stops."
        pygame.quit()
