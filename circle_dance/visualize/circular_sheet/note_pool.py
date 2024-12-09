# circular sheet visualization: note pools
# manages the notes on a sheet and the adding of new notes

import math
from abc import ABC, abstractmethod

import numpy as np
import numpy.typing as npt
import pygame
from scipy import ndimage

from circle_dance.visualize import Drawable
from circle_dance.visualize.circular_sheet import (
    ArcNote,
    ArcNote_Legacy,
    DotNote,
    Note,
    SimpleArcNote,
    config,
    utils,
)
from circle_dance.visualize.draw import draw_circular_gradient
from circle_dance.visualize.types import T_COLOR


class NotePool(Drawable, ABC):

    def __init__(self, surface: pygame.Surface, note_base_radius: int, note_size: int, note_color: T_COLOR):
        """Note pool base class.

        Manages the notes and allows to add more notes.

        Args:
            surface: the surface the notes are drawn upon
            note_base_radius: the base radius of the notes
                the first note of the scale will be placed on this radius, all other accordingly
            note_size: the base size of the notes
            note_color: the color of the notes
        """
        super().__init__(surface)

        self.note_size = note_size  # node_size = self.dist_between_sheet_lines // 2  # two notes per line, as half-tones are possible
        self.note_color = note_color
        self.note_base_radius = note_base_radius  # self.radius_outer

        self.notes: list[Note] = []

    @abstractmethod
    def add_note(self, note: int, onset: float, conclusion: float, energy: float):
        """Add a note to the note pool.

        This method takes the note details as returned by a method in `circle_dance.audio.process` and creates the
        appropriate note. The type of note added depends on the actual note pool implementation.

        Args:
            note: note id, aka a number between 0 and 12
            onset: onset time of the note, in seconds
            conclusion: conclusion time of the note, in seconds
            energy: chroma energy of the note, a value between 0 and 1
        """
        pass

    def draw(self, t: float) -> None:
        self._remove_dead_notes(t)
        for note in self.notes:
            note.draw(t)

    def _remove_dead_notes(self, t: float):
        self.notes = [n for n in self.notes if n.is_alive(t)]

    def _get_note_radius(self, note: int):
        "Compute the appropriate radius location of the note."
        return (
            self.note_base_radius - (11 - note) * self.note_size
        )  # first note is placed on radius, then half-line steps; reversed order to get deeper notes on the inner radius


class DotNotePool(NotePool):

    def add_note(self, note: int, onset: float, conclusion: float, energy: float):
        # compute note location from onset and base radius
        radius = self._get_note_radius(note)
        angle = utils.get_angle_at_time(onset)  # note position of circle according to it's onset
        x = self.surface.get_width() // 2 + radius * math.cos(angle)
        y = self.surface.get_height() // 2 + radius * math.sin(angle)

        self.notes.append(
            DotNote(
                self.surface,
                x,
                y,
                self.note_size,
                self.note_color,
                onset,
                config.rotation_period - 1,
            )
        )


class ArcNotePool(NotePool):

    def __init__(self, surface: pygame.Surface, note_base_radius: int, note_size: int, note_color: T_COLOR):
        super().__init__(surface, note_base_radius, note_size, note_color)

        # prepare an pixel-wise alpha enabled surface for the notes to be drawn on
        self.surface_notes = pygame.Surface((self.surface.get_width(), self.surface.get_height()), pygame.SRCALPHA)
        self.arr = np.zeros(self.surface_notes.get_size(), dtype=np.bool)

    def add_note(self, note: int, onset: float, conclusion: float, energy: float):
        # compute note radius position from base radius
        radius = self._get_note_radius(note)

        # if there is already a note on the same sheet line (same radius position) and with overlapping [onset, conclusion] time
        # then update that note's conclusion time
        for n in self.notes:
            assert isinstance(n, ArcNote)
            if n.radius == radius and onset <= n.conclusion:
                n.conclusion = conclusion
                return

        # otherwise add a new ArcNote
        self.notes.append(
            ArcNote(
                self.surface_notes, radius, 1, self.note_size, onset, conclusion, config.rotation_period - 1, self.arr
            )
        )

    def draw(self, t: float) -> None:
        self.surface_notes.fill((0, 0, 0, 0))  # clear note surface; make transparent
        self.arr.fill(0)  # clear array
        print("#note:", len(self.notes))
        super().draw(t)  # let the notes draw their b/w arcs

        # get pixel values from surface (they denote the locations of the arc pixels)
        # arc_pixels = pygame.surfarray.array2d(self.surface_notes).astype(np.bool)
        arc_pixels = self.arr

        print("sum:", arc_pixels.sum())

        # create color image (3 channels, no alpha)
        color_channels = np.dstack(
            [
                arc_pixels * self.note_color[0],
                arc_pixels * self.note_color[1],
                arc_pixels * self.note_color[2],
            ]
        )

        # write color values to note surface
        pygame.surfarray.blit_array(self.surface_notes, color_channels)

        # write alpha channel to note surface
        # Note: not save in var, as saving in var would acquire surface lock; can only be released with del var
        pygame.surfarray.pixels_alpha(self.surface_notes)[:] = ArcNotePool._make_alpha_channel(t, arc_pixels)

        self.surface.blit(self.surface_notes, (0, 0))  # blit note image onto the main pool surface

    @staticmethod
    def _make_alpha_channel(t: float, arc_pixels: npt.NDArray[np.bool]) -> npt.NDArray[np.uint8]:
        """Create the alpha channel for the current time.

        The channel will have a circular gradient alpha where there are note pixels, starting at the angle of `t`.
        The rest of the channel is set to full transparency.

        Args:
            t: current time in seconds
            arc_pixels: boolean array denoting the pixels of the arc
        """
        t_rad = utils.get_angle_at_time(t)
        lt_factor = (
            config.rotation_period - 1
        ) / config.rotation_period - 1  # lifetime as factor of total rotation period
        alpha_channel = draw_circular_gradient(*arc_pixels.shape)
        alpha_channel = np.clip(
            alpha_channel / lt_factor, 0, 1
        )  # limit gradient's maximum transparency to factor of complete circle
        alpha_channel = ndimage.rotate(
            alpha_channel, -np.rad2deg(t_rad), reshape=False, mode="nearest"
        )  # rotate transparency gradient to current time's location
        alpha_channel = ((1 - alpha_channel) * 255).astype(np.uint8)
        alpha_channel[~arc_pixels] = 0  # set alpha to max transparency where there is no arc

        return alpha_channel


class SimpleArcNotePool(NotePool):

    def add_note(self, note: int, onset: float, conclusion: float, energy: float):
        # compute note radius position from base radius
        radius = self._get_note_radius(note)

        # if there is already a note on the same sheet line (same radius position) and with overlapping [onset, conclusion] time
        # then update that note's conclusion time
        for n in self.notes:
            assert isinstance(n, SimpleArcNote)
            if n.radius == radius and onset <= n.conclusion:
                n.conclusion = conclusion
                return

        # otherwise add a new ArcNote
        self.notes.append(
            SimpleArcNote(
                self.surface,
                radius,
                self.note_size,
                self.note_color,
                onset,
                conclusion,
                config.rotation_period - 1,
            )
        )


class ArcNotePool_Legacy(NotePool):

    def add_note(self, note: int, onset: float, conclusion: float, energy: float):
        # compute note radius position from base radius
        radius = self._get_note_radius(note)

        # if there is already a note on the same sheet line (same radius position) and with overlapping [onset, conclusion] time
        # then update that note's conclusion time
        for n in self.notes:
            assert isinstance(n, ArcNote)
            if n.radius == radius and onset <= n.conclusion:
                n.conclusion = conclusion
                return

        # otherwise add a new ArcNote
        self.notes.append(
            ArcNote_Legacy(
                self.surface,
                radius,
                self.note_size,
                self.note_color,
                onset,
                conclusion,
                config.rotation_period - 1,
            )
        )
