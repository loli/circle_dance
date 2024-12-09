# circular sheet visualization: rotating pointer

import math

import pygame

from circle_dance.visualize import Drawable
from circle_dance.visualize.circular_sheet import utils
from circle_dance.visualize.types import T_COLOR

LINE_WIDTH = 2


class Pointer(Drawable):
    def __init__(self, surface: pygame.Surface, radius: int, color: T_COLOR):
        """A rotating pointer that indicates the current position in the circular sheet."""
        self.surface = surface
        self.center = (surface.get_width() // 2, surface.get_height() // 2)
        self.radius = radius
        self.color = color

    def draw(self, t: float):
        """Draw the pointer at the position corresponding to `t`."""
        angle = utils.get_angle_at_time(t)
        self.__draw_pointer(angle)

    def __draw_pointer(self, angle: float):
        """Draw a line from the center to the radius' circumference at the current angle.

        Args:
            angle: position of the line, expressed as a circle's angle in radians
        """
        end_x = self.center[0] + self.radius * math.cos(angle)
        end_y = self.center[1] + self.radius * math.sin(angle)
        pygame.draw.line(self.surface, self.color, self.center, (end_x, end_y), LINE_WIDTH)
