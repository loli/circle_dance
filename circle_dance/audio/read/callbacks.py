# audio stream callback functions to be used in the stream reader
# these wrap the audio processing functionality to be usable in the stream_reader

import logging

import librosa
import numpy as np
import numpy.typing as npt

from circle_dance.audio import process

logger = logging.getLogger(__name__)


# Note: prefers steam_reader with
#    buffer_replenish_multiplier = 3
#    buffer_carryover_multiplier = 8
def extract_node_onsets_callback(
    buffer: npt.NDArray,
    sr: float,
    stream_clock: float,
    carryover_samples: int,
    carryover_time_sec: float,
    threshold: float = 0.25,
    slide_length: int = 512,
    peak_detection_delay_frames: int = 1,
) -> npt.NDArray:
    """
    Extracts note onsets from an audio buffer and adds them to a queue.

    This function processes an audio buffer to detect note onsets and adds the detected notes to a queue.
    It adjusts the onset times to account for the carryover samples from the previous iteration/buffer.

    Usage:
        `notes_producer(lambda *args, **kwargs: process_buffer_callback(*args, **kwargs, threshold=0.25), ...)`

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
        slide_length: slide_length, hop_length, window_length for all filters
        peak_detection_delay_frames: a detected peak is allowed to be up to this many frames inside the carry over
            samples; alivates problem of missing peaks due to the small new sample sizes

    Returns:
        Notes cleaned from carryover effects.
    """
    # extract notes
    notes_with_onsets = process.extract_note_onsets(
        buffer.astype(float), sr=sr, threshold=threshold, slide_length=slide_length
    )

    if len(notes_with_onsets) == 0:
        return np.zeros(0)

    # remove carryover part and adjust times
    notes_with_onsets[:, 1:2] -= carryover_time_sec  # adjust onset times
    # remove notes with onset in the past (obsolete, too few peaks detected in short chunk duration)
    # notes_with_onsets = notes_with_onsets[notes_with_onsets[:, 1] > 0]
    # remove notes with onset furether in the past than the allowed peak delay
    peak_detection_delay_s = librosa.frames_to_time(peak_detection_delay_frames, sr=sr, hop_length=slide_length)
    notes_with_onsets = notes_with_onsets[notes_with_onsets[:, 1] > -peak_detection_delay_s]

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
    threshold: float = 0.25,
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
