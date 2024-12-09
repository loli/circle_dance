# circular sheet visualization: notes

import logging
import math
from abc import ABC, abstractmethod

import numpy as np
import pygame

from circle_dance.visualize import Drawable
from circle_dance.visualize.circular_sheet import utils
from circle_dance.visualize.draw import draw_circle_alpha, draw_cone_arc
from circle_dance.visualize.types import T_COLOR

logger = logging.getLogger(__name__)


class Note(Drawable, ABC):

    @abstractmethod
    def is_alive(self, t: float) -> bool:
        """Check if the note is still alive.

        Args:
            t: current time in seconds

        Returns:
            whether or not the note has reached the end of it's lifetime
        """
        pass


class DotNote(Note):
    def __init__(
        self, surface: pygame.Surface, x: float, y: float, size: int, color: T_COLOR, onset: float, lifetime: float
    ):
        """Define a note on a surfaced visualized as a dot/circle.

        Args:
            screen: surface to draw on
            x: x-coordinate of the note
            y: y-coordinate of the note
            size: size of the note
            color: color of the note
            onset: time when the note is played; seconds
            lifetime: time the note should be displayed for; seconds
        """
        super().__init__(surface)

        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.onset = onset
        self.lifetime = lifetime

    def is_alive(self, t: float) -> bool:
        return self.onset + self.lifetime >= t

    def draw(self, t: float) -> None:
        """Draw a circle representing the note.

        Args:
            t: current time in seconds
        """
        if t >= self.onset and t <= self.onset + self.lifetime:
            strength = 1 - (t - self.onset) / self.lifetime
            self.__draw_note(strength)

    def __draw_note(self, strength: float) -> None:
        """Draw a circle representing the note.

        Args:
            strength: strength of the note, used to determine its transparency and size
        """
        alpha = int(255 * strength)
        color = self.color[:3] + (alpha,)
        size = self.size * ((1 - strength) * 10 + 1)
        draw_circle_alpha(self.surface, color, (self.x, self.y), size)
        # pygame.draw.circle(self.surface, color, (self.x, self.y), size)


class ArcNote(Note):
    def __init__(
        self,
        surface: pygame.Surface,
        radius: float,
        size_min: int,
        size_max: int,
        onset: float,
        conclusion: float,
        lifetime: float,
        arr,
    ):
        """Define a note on a surface visualized as a duration arc.

        Args:
            screen: surface to draw on
            radius: radius of the note arc
            size_min: minimum width of arc (at pointy end)
            size_max: maximum width of arc (at blunt end, at end of it's lifetimes)
            color: color of the note
            onset: time when the note is played; seconds
            conclusion: time when the note is no longer heard; seconds
            lifetime: time the note should be displayed for; seconds
        """
        super().__init__(surface)

        self.radius = radius
        self.size_min = size_min
        self.size_max = size_max
        self.onset = onset
        self.conclusion = conclusion
        self.lifetime = lifetime

        self.arr = arr

        self.onset_angle = utils.get_angle_at_time(self.onset)
        self.surface_width = self.surface.get_width()
        self.surface_height = self.surface.get_height()
        self.center = self.surface_height // 2, self.surface_width // 2

    def is_alive(self, t: float) -> bool:
        return t - self.conclusion < self.lifetime

    def draw(self, t: float) -> None:
        """Draw an arc line representing a note with duration.

        Args:
            t: current time in seconds
        """
        if t >= self.onset and t - self.conclusion < self.lifetime:
            self.__draw_note(t)

    def __draw_note(self, t: float):
        """Draw a cone-shaped arc with gradual transparency by drawing multiple dots along an arc line.

        Args:
            t: current time in seconds
        """
        assert t > self.onset, "arc's onset lies in the future"
        assert t - self.conclusion < self.lifetime, "arc's lifetime has expired and cannot be drawn"
        assert self.conclusion > self.onset, "arc's length is zero or less"

        # derived parameters
        t_arc_start = min(t, self.conclusion)
        t_arc_start_rad = utils.get_angle_at_time(t_arc_start)
        t_arc_end = max(self.onset, t - self.lifetime)
        t_arc_end_rad = utils.get_angle_at_time(t_arc_end)

        width_arc_start = (t - t_arc_start) / self.lifetime * (self.size_max - self.size_min) + self.size_min
        width_arc_end = (t - t_arc_end) / self.lifetime * (self.size_max - self.size_min) + self.size_min

        print("start-end", t_arc_start, t_arc_end)
        print("arr.shape", self.arr.shape)
        print("radius", self.radius)
        print("center", self.center)

        # construct cone shape arc
        # surface_arr = pygame.surfarray.array3d(self.surface)
        return draw_cone_arc(
            self.arr,
            self.center,
            self.radius,
            t_arc_end_rad,
            t_arc_start_rad,  # paints from wide end clock-wise
            width_arc_end,
            width_arc_start,
        )
        # del surface_arr


class SimpleArcNote(Note):
    def __init__(
        self,
        surface: pygame.Surface,
        radius: float,
        size: int,
        color: T_COLOR,
        onset: float,
        conclusion: float,
        lifetime: float,
    ):
        """Define a note on a surface visualized as a duration arc.

        Args:
            screen: surface to draw on
            radius: radius of the note arc
            size: size of the note
            color: color of the note
            onset: time when the note is played; seconds
            conclusion: time when the note is no longer heard; seconds
            lifetime: time the note should be displayed for; seconds
        """
        super().__init__(surface)

        self.radius = radius
        self.size = size
        self.color = color
        self.onset = onset
        self.conclusion = conclusion
        self.lifetime = lifetime

        self.onset_angle = utils.get_angle_at_time(self.onset)

    def is_alive(self, t: float) -> bool:
        return self.onset + self.lifetime >= t

    def draw(self, t: float) -> None:
        """Draw an arc line representing a note with duration.

        Args:
            t: current time in seconds
        """
        if t >= self.onset and t <= self.onset + self.lifetime:
            self.__draw_note(t)

    def __draw_note(self, t: float):
        """Draw a simple arc line.

        Args:
            t: current time in seconds
        """
        assert t > self.onset
        assert t - self.onset <= self.lifetime

        # derived parameters
        t_arc_start = min(t, self.conclusion)
        t_arc_start_rad = utils.get_angle_at_time(t_arc_start)
        t_arc_end = max(self.onset, t - self.lifetime)
        t_arc_end_rad = utils.get_angle_at_time(t_arc_end)

        w, h = self.surface.get_size()
        radius_corrected = self.radius + self.size // 2  # arc paints width only inwards
        rect = pygame.Rect(
            w // 2 - radius_corrected, h // 2 - radius_corrected, 2 * radius_corrected, 2 * radius_corrected
        )
        # pygame.draw.arc(self.surface, self.color, rect, -np.deg2rad(45), np.deg2rad(0), self.size)
        pygame.draw.arc(
            self.surface, self.color, rect, 2 * np.pi - t_arc_start_rad, 2 * np.pi - t_arc_end_rad, self.size
        )


class ArcNote_Legacy(Note):
    def __init__(
        self,
        surface: pygame.Surface,
        radius: float,
        size: int,
        color: T_COLOR,
        onset: float,
        conclusion: float,
        lifetime: float,
    ):
        """Define a note on a surface visualized as a duration arc.

        Args:
            screen: surface to draw on
            radius: radius of the note arc
            size: size of the note
            color: color of the note
            onset: time when the note is played; seconds
            conclusion: time when the note is no longer heard; seconds
            lifetime: time the note should be displayed for; seconds
        """
        super().__init__(surface)

        self.radius = radius
        self.size = size
        self.color = color
        self.onset = onset
        self.conclusion = conclusion
        self.lifetime = lifetime

        self.onset_angle = utils.get_angle_at_time(self.onset)

    def is_alive(self, t: float) -> bool:
        return self.onset + self.lifetime >= t

    def draw(self, t: float) -> None:
        """Draw an arc line representing a note with duration.

        Args:
            t: current time in seconds
        """
        if t >= self.onset and t <= self.onset + self.lifetime:
            self.__draw_note(t, min_width=max(3, self.size // 5), max_width=self.size * 3)

    def __draw_note(self, t: float, min_width: int, max_width: int, max_dots: int = 1000):
        """Draw a cone-shaped arc with gradual transparency by drawing multiple dots along an arc line.

        Args:
            t: current time in seconds
            min_width: width of the arc at it's pointy end
            max_width: width of the arc at it's blunt end
            max_dots: maximum number of dots to utilize to simulate the arc; default 1000
        """
        assert t > self.onset
        assert t - self.onset <= self.lifetime

        # start & end times of note arc @ current time t, clockwise
        t_start = self.onset
        t_end = min(t, self.conclusion)

        # visualization strength at start & end of note arc
        # depends on location in range [t - lifetime, t]
        # the more distant from t a location, the less visualization strength
        str_start = 1 - max(0, t - t_start) / self.lifetime
        str_end = 1 - max(0, t - t_end) / self.lifetime

        alpha_start = 255 * str_start
        alpha_end = 255 * str_end

        width_start = min_width + (1 - str_start) * (max_width - min_width)
        width_end = min_width + (1 - str_end) * (max_width - min_width)

        # number of dots to actually draw depends on note arc length @ t
        # the maximum number of dots are only used when arc length maximum, aka equal lifetime
        n_dots = max(1, int((t_end - t_start) / self.lifetime * max_dots))

        # loop vars
        width_delta = (width_end - width_start) / n_dots
        alpha_delta = (alpha_end - alpha_start) / n_dots

        dot_id = 0
        for dot_t in np.linspace(t_start, t_end, n_dots):
            x = int(
                self.surface.get_width() // 2
                + self.radius * math.sin(utils.get_angle_at_time(dot_t) + math.radians(90))
            )
            y = int(
                self.surface.get_height() // 2
                - self.radius * math.cos(utils.get_angle_at_time(dot_t) + math.radians(90))
            )

            dot_color = self.color[:3] + (int(alpha_start + dot_id * alpha_delta),)
            dot_width = int(width_start + dot_id * width_delta)

            # pygame.draw.circle(self.surface, dot_color, (x, y), dot_width)
            draw_circle_alpha(self.surface, dot_color, (x, y), dot_width)

            dot_id += 1
