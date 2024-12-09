import audioflux as af
import librosa
import numpy as np


def extract_note_onsets(y, sr: float, threshold: float = 0.9):
    """Extract the note onset from each frame of audio data.

    Args:
        y: audio data
        sr: sampling rate of the audio data
        threshold: the chroma energy threshold for considering a note as active; between 0 and 1

    Returns:
        the detect N note onsets and their onset time; shape=(N, 4),
            with columns=(note_id, onset(sec), np.nan, chroma_energy[0,1])
    """
    # Compute the chromagram
    # note: audioflux is 10x faster than librosa
    obj = af.CQT(num=12 * 7, samplate=int(sr), low_fre=af.utils.note_to_hz("C1"), bin_per_octave=12, slide_length=512)
    chroma = obj.chroma(obj.cqt(y), chroma_num=12)
    # chroma = librosa.feature.chroma_cqt(y=y, sr=sr, n_chroma=12)

    # Compute onset strength
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    # Detect note onsets
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, normalize=True, backtrack=True)

    # Extract notes at onset frames
    notes_with_onsets = []
    for frame in onset_frames:
        chroma_frame = chroma[:, frame]
        frame_time = librosa.frames_to_time(frame, sr=sr)

        # Find all notes above the threshold
        active_note_found = False
        for i, magnitude in enumerate(chroma_frame):
            if magnitude > threshold:
                notes_with_onsets.append((i % 12, frame_time, np.nan, magnitude))
                active_note_found = True

        # If no notes are above threshold, take the highest one
        if not active_note_found:
            max_index = int(np.argmax(chroma_frame))
            notes_with_onsets.append((max_index % 12, frame_time, np.nan, chroma_frame[max_index]))

    return np.asarray(notes_with_onsets)
