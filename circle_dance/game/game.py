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

    def __init__(self, windowed: bool = False, fps: int = 40) -> None:
        """Game implementation.

        Takes care of initializing pygame, prepares the screen, maintains the synchronization clock, and provides a
        callback interface for modules to register to.

        Also takes care of teardown and all global functionality, such as processing quit commands.

        Args:
            windowed: run game in windowed mode instead of fullscreen
            fps: set to a value higher than 0 to limit framerate

        !TBD:
            - add some parameters (e.g. fullscreen, window size, window title)
            - add some logging
            - add some way to register event callbacks (e.g. key press, mouse click)
            - add some error handling (quit game gracefully)
            - callbacks registration also need to provide module name for better debug logging
            - print debug info on click duration, e.g. every 10 clicks the average or such
        """
        self.windowed = windowed
        self.fps = fps
        self.clock = 0.0

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
        #clock = pygame.time.get_ticks() / 1000  # in seconds, passed since init()
        gclock = pygame.time.Clock()
        running = True

        # pre-run callbacks
        self._pre_run()
        [c(self, self.clock) for c in self.__callbacks_pre_run]

        while running:
            # exit on ESC and pygame.QUIT
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                    self.display_controls()
                elif event.type == pygame.KEYDOWN and event.key in self.__callbacks_keydown:
                    self.__callbacks_keydown[event.key]["callback"](self)  # handle keydown callbacks
                    self.logger.display_line(f"{self.__callbacks_keydown[event.key]['name']} = {self.__callbacks_keydown[event.key]['get']()}")

            # update clock
            #clock = pygame.time.get_ticks() / 1000

            # update by calling update on each module
            # mainly used to update the screen
            [c(self, self.clock) for c in self.__callbacks_update]

            pygame.display.flip()

            # check if termination desire signaled by any module
            if functools.reduce(lambda a, b: a or b, [c(self, self.clock) for c in self.__callbacks_should_terminate]):
                running = False
                
            print("g:clock(s):", self.clock)
            print("g:fps:", gclock.get_fps())
            gclock.tick(self.fps)
            self.clock += gclock.get_time() / 1000

        # post-run callbacks
        [c(self, self.clock) for c in self.__callbacks_post_run]

        # teardown
        [c(self) for c in self.__callbacks_teardown]
        self._teardown()
        
    def set_clock(self, time: float) -> None:
        self.clock = time

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

    def register_keydown_callback(self, name: str, key: int, callback: T_CALLBACK_KEYDOWN, get: T_CALLBACK_KEYDOWN) -> None:
        self.__callbacks_keydown[key] = {"name": name, "callback": callback, "get": get}

    def _setup(self) -> None:
        "Game setup, before the clock starts."
        pygame.init()
        pygame.font.init()

        # get screen resolution
        info = pygame.display.Info()
        screen_width, screen_height = info.current_w, info.current_h

        # game display setup
        if self.windowed:
            screen = pygame.display.set_mode((screen_width // 2, screen_height // 2), pygame.NOFRAME)
        else:
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("Circular Music Sheet Animation")

        self.screen = screen
        self.logger = LogDisplay(self)  # must be initialized last, as should be last update to call
        
    def _pre_run(self) -> None:
        "Game pre-run, before the clock starts."
        self.display_controls()  # once at start

    def _teardown(self) -> None:
        "Game teardown, after the clock stops."
        pygame.quit()
        
    def display_controls(self) -> None:
        lines = ["Controls:"]
        for k in self.__callbacks_keydown:
            lines.append(f"{pygame.key.name(k)}: {self.__callbacks_keydown[k]['name']}")
        self.logger.display_lines(lines)


class LogDisplay():

    def __init__(self, g: Game, t_visible: float = 1.):
        """Log display module.

        Provides a surface on which text can be displayed.
        This module is intended to be always active in each game.
        The display disappears after some time.


        Args:
            t_visible: visibility on screen in seconds
        """
        self.t_visible = t_visible
        
        self.font = pygame.font.SysFont('mono', 14)
        self.color = (255, 255, 255)
        self.bg_color = (0, 0, 0)
        
        self.make_visible = False
        self.t_became_visible = 0
        self.lines = []
        
        g.register_update_callback(self._update)

    def display_lines(self, lines: list[str]):
        self.make_visible = True
        self.lines = lines
        
    def display_line(self, line: str):
        self.display_lines([line])

    def _update(self, g: Game, clock: float):
        if self.make_visible:
            self.t_became_visible = clock
            self.make_visible = False
        if clock - self.t_became_visible < self.t_visible:
            y = 10
            for line in self.lines:
                text_surface = self.font.render(line, True, self.color, self.bg_color)
                g.screen.blit(text_surface, (10, y))
                y += text_surface.get_height()
