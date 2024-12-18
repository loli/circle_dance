# stream reader

import logging
import queue
import threading
from queue import Empty, Full
from typing import Callable, TypeAlias

import numpy as np
import numpy.typing as npt
import pyaudio

logger = logging.getLogger(__name__)


# !NOTE:
# When the processing of an audio buffer has a runtime > buffer_replenish_multiplier * CHUNK / RATE, then the notes will slowly get more and more delayed
# potential solution: discard older notes, always empty audio buffer until no more to get
# !NOTE:
# buffer_replenish_multiplier * CHUNK / RATE is minimum delay between displays - should be <= 0.02s to be perceived as real time
# !NOTE:
# Doubling the RATE effectively halves the CHUNK

# e.g. def process_buffer(buffer, sr, stream_clock, carryover_samples, carryover_time_sec) -> list
T_CALLBACK_PROCESS_BUFFER: TypeAlias = Callable[
    [npt.NDArray[np.int16], float, float, int, float], npt.NDArray[np.float32]
]

# Main stream parameters
CHUNK = 1024  # 1024 Number of frames per buffer
FORMAT = pyaudio.paInt16  # Format of the audio samples
CHANNELS = 1  # Number of channels (1 for mono, 2 for stereo)
RATE = 44100  # 44100  # 22050 # Sample rate (samples per second)


def stream_reader(
    process_buffer_callback: T_CALLBACK_PROCESS_BUFFER,
    queue: queue.Queue,
    close_request_event: threading.Event,
    buffer_replenish_multiplier: int,
    buffer_carryover_multiplier: int,
    *args,  # passed to process_buffer_callback
    **kwargs,  # passed to process_buffer_callback
):
    """Producer that produces notes from an audio stream. Meant to be run with multithreading.

    Note:
        Does not run well with multiprocessing. Causes input buffer overflow.

    Args:
        process_buffer_callback: function to call to process each buffer
        queue: the queue to put the notes into
        close_request_event: closes itself once this event has been triggered
        buffer_replenish_multiplier: wait until we obtained this times CHUNK of new audio data until we process the buffer
        buffer_carryover_multiplier: carry over this times CHUNK of audio data from last call to the next call
    """
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    stream_clock = 0.0  # position in stream; and position in buffer after carryover samples; in seconds
    buffer = np.array([], dtype=np.int16)

    # read steam, process audio data, and write note to queue
    try:
        while not close_request_event.is_set():
            carryover_offset_samples = len(buffer)
            carryover_offset_sec = carryover_offset_samples / RATE
            # print("sp: carryover_offset_sec", carryover_offset_sec)

            # fill up buffer
            while len(buffer) - carryover_offset_samples < CHUNK * buffer_replenish_multiplier:
                # Read a chunk of data from the stream
                data = stream.read(CHUNK)
                # Convert the byte data to numpy array
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                # Append the new chunk to the buffer
                buffer = np.append(buffer, audio_chunk)

            # callback buffer processor
            items = process_buffer_callback(
                buffer,
                RATE,
                stream_clock,
                carryover_offset_samples,
                carryover_offset_sec,
                *args,
                **kwargs,
            )

            # put items into queue, keeping newest items
            for item in items:
                if queue.full():  # make one attempt at removing the oldest note in the queue if full
                    try:
                        logger.warn("queue full, trying to discard oldest item")
                        queue.get_nowait()
                    except Empty:
                        pass
                try:  # try, discard if didn't work
                    queue.put_nowait(item)
                except Full:
                    logger.warn("discarded item due to full queue")
                    pass

            # update stream clock
            stream_clock += len(buffer) / RATE - carryover_offset_sec  # subtract time of carryover samples

            # keep something at the end of the buffer for better continuity
            buffer = buffer[-CHUNK * buffer_carryover_multiplier :]
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
