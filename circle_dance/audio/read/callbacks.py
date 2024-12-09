# audio stream callback functions to be used in the stream reader
# these wrap the audio processing functionality to be usable in the stream_reader

import logging

import numpy.typing as npt

from circle_dance.audio import process

logger = logging.getLogger(__name__)


# Note: prefers steam_reader with
#    buffer_replenish_multiplier = 5
#    buffer_carryover_multiplier = 20
def extract_node_onsets_callback(
    buffer: npt.NDArray,
    sr: float,
    stream_clock: float,
    carryover_samples: int,
    carryover_time_sec: float,
    threshold: float = 0.99,
) -> npt.NDArray:
    """
    Extracts note onsets from an audio buffer and adds them to a queue.

    This function processes an audio buffer to detect note onsets and adds the detected notes to a queue.
    It adjusts the onset times to account for the carryover samples from the previous iteration/buffer.

    Usage:
        `notes_producer(lambda *args, **kwargs: process_buffer_callback(*args, **kwargs, threshold=0.9), ...)`

    Args:
        queue: The queue to put the detected notes into.
        buffer: The audio buffer containing the audio data. First part is carried over form previous iteration/buffer,
            the remaining samples are new.
        sr: The sampling rate of the audio.
        stream_clock: The current position in the audio stream after the carry over samples, in seconds.
        carryover_samples: the number of samples at the beginning of the buffer that are repeated the previous
            iteration/buffer
        carryover_time_sec: the time in seconds of the carryover samples
        threshold: The energy threshold for considering a note as active, between 0 and 1.

    Returns:
        Notes cleaned from carryover effects.
    """
    # extract notes
    notes_with_onsets = process.extract_note_onsets(buffer.astype(float), sr=sr, threshold=threshold)

    # remove carryover part and adjust times
    notes_with_onsets[:, 1:2] -= carryover_time_sec  # adjust onset times
    notes_with_onsets = notes_with_onsets[notes_with_onsets[:, 1] > 0]  # remove notes wiht onset in the past

    # add stream clock to times to get real clock times of notes
    notes_with_onsets[:, 1:2] += stream_clock

    return notes_with_onsets


# Note: prefers steam_reader with
#    buffer_replenish_multiplier = 1
#    buffer_carryover_multiplier = 20
def extract_note_durations_callback(
    buffer: npt.NDArray,
    sr: float,
    stream_clock: float,
    carryover_samples: int,
    carryover_time_sec: float,
    threshold: float = 0.99,
) -> npt.NDArray:
    # extract notes
    notes_with_durations = process.extract_note_durations(buffer.astype(float), sr=sr, thr=threshold)

    # remove carryover part and adjust times
    notes_with_durations[:, 1:3] -= carryover_time_sec  # adjust onset and conclusion times
    notes_with_durations = notes_with_durations[
        notes_with_durations[:, 2] > 0
    ]  # remove notes with duration in the past
    notes_with_durations = notes_with_durations.clip(min=0)  # clip onset

    # add stream clock to times to get real clock times of notes
    notes_with_durations[:, 1:3] += stream_clock

    return notes_with_durations
