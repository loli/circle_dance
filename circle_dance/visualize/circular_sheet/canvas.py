# circular sheet visualization: main canvas

import pygame

from circle_dance.visualize import Drawable
from circle_dance.visualize.circular_sheet import NotePool, Pointer, Sheet, config
from circle_dance.visualize.types import T_COLOR


class Canvas(Drawable):
    def __init__(
        self, surface: pygame.Surface, n_sheets: int, note_pool: type[NotePool], bg_color: T_COLOR = config.BLACK
    ):
        """The main circular sheet visualization canvas.

        Takes care of coordinating all the contained components.

        Args:
            surface: surface to draw on
            n_sheets: no of circular sheets to display and support
            note_pool: NotePool implementation to use for the sheets
            bg_color: background color of the canvas
        """
        super().__init__(surface)

        assert n_sheets > 0, "At least one sheet must be drawn."

        self.bg_color = bg_color
        self.radius_outer = (
            min(surface.get_width(), surface.get_height()) // 2 - config.radius_margin_outer
        )  # outermost radius to draw in
        self.radius_inner = config.radius_margin_inner  # innermost radius to draw in

        # surface the sub-components draw on, with alpha support
        self.surface_components = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)

        # init sub-components
        self.sheets: list[Sheet] = []
        dist_between_sheet_lines = min(
            config.max_dist_between_sheet_lines,
            (
                (self.radius_outer - self.radius_inner)
                // n_sheets
                // (config.n_sheet_lines + config.n_lines_space_between_sheets)
            ),
        )
        for i in range(n_sheets):
            sheet_radius_outer = self.radius_outer - i * config.n_sheet_lines * (
                dist_between_sheet_lines + config.n_lines_space_between_sheets
            )
            self.sheets.append(
                Sheet(
                    self.surface_components,
                    sheet_radius_outer,
                    config.n_sheet_lines,
                    dist_between_sheet_lines,
                    config.sheet_colors[i],
                    note_pool,
                )
            )

        self.pointer: Pointer = Pointer(self.surface_components, self.radius_outer, config.PINK)

    def draw(self, t: float) -> None:
        self.surface.fill(self.bg_color)  # fill in surface
        self.surface_components.fill((0, 0, 0, 0))  # clear sub-components surface

        self.pointer.draw(t)
        for sheet in self.sheets:
            sheet.draw(t)

        # blit the sub-components surface onto the surface
        self.surface.blit(self.surface_components, self.surface_components.get_rect())

    def add_note(self, sheet_id: int, note: int, onset: float, conclusion: float, energy: float):
        "Add a note to an underlying sheet."
        self.sheets[sheet_id].note_pool.add_note(note, onset, conclusion, energy)
