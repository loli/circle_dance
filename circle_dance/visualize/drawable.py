# base class for all drawable objects

from abc import ABC, abstractmethod

import pygame


class Drawable(ABC):

    def __init__(self, surface: pygame.Surface):
        """A drawable.

        Args:
            surface: the surface this drawable draws itself on
        """
        self.surface = surface

    @abstractmethod
    def draw(self, t: float) -> None:
        pass
