# circular sheet visualization: note sheet

import pygame

from circle_dance.visualize import Drawable
from circle_dance.visualize.circular_sheet import NotePool
from circle_dance.visualize.types import T_COLOR

LINE_WIDTH = 1


class Sheet(Drawable):
    def __init__(
        self,
        surface: pygame.Surface,
        radius_outer: int,
        n_sheet_lines: int,
        dist_between_sheet_lines: int,
        color: T_COLOR,
        note_pool: type[NotePool],
    ):
        """Define a (circular) sheet music on the screen.

        Draws multiple lines. Can generate notes which are drawn among the lines.

        Args:
            screen: surface to draw on
            radius_outer: outer radius of the sheet, corresponds to the first line
            n_sheet_lines: number of lines in the sheet
            dist_between_sheet_lines: distance between each line in the sheet
            color: color of the sheet lines
            note_pool: NotePool implementation to use for this sheet
        """
        super().__init__(surface)

        self.radius_outer = radius_outer
        self.n_sheet_lines = n_sheet_lines
        self.dist_between_sheet_lines = dist_between_sheet_lines
        self.color = color
        self.center = (surface.get_width() // 2, surface.get_height() // 2)

        self.note_pool = note_pool(
            self.surface,
            self.radius_outer,
            self.dist_between_sheet_lines // 2,  # two notes per line, as half-tones are possible
            self.color,
        )

    def draw(self, t: float) -> None:
        self.__draw_sheet()
        self.note_pool.draw(t)

    def __draw_sheet(self):
        """Draw the lines of a circular music sheet.

        Draws `n_sheet_lines` of color `color` starting at `radius_outer` inwards with `dist_between_sheet_lines` between the lines.
        """
        for j in range(self.n_sheet_lines):
            pygame.draw.circle(
                self.surface,
                self.color,
                self.center,
                self.radius_outer - j * self.dist_between_sheet_lines,
                width=LINE_WIDTH,
            )
