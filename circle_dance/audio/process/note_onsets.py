import audioflux as af
import librosa
import numpy as np


def extract_note_onsets(y, sr: float, threshold: float = 0.25, slide_length: int = 512):
    """Extract the note onset from each frame of audio data.

    Args:
        y: audio data
        sr: sampling rate of the audio data
        threshold: the chroma energy threshold for considering a note as active; between 0 and 1
        slide_length: slide_length (audioflux), hop_length (librosa), window length (fft)

    Returns:
        the detect N note onsets and their onset time; shape=(N, 4),
            with columns=(note_id, onset(sec), np.nan, chroma_energy[0,1])
    """
    # Compute the chromagram
    cqt_obj = af.CQT(
        num=12 * 7,
        samplate=int(sr),
        low_fre=af.utils.note_to_hz("C1"),
        bin_per_octave=12,
        slide_length=slide_length,
        normal_type=af.type.SpectralFilterBankNormalType.AREA,
    )
    y_chroma = cqt_obj.chroma(
        cqt_obj.cqt(y),
        chroma_num=12,
        data_type=af.type.SpectralDataType.POWER,
        norm_type=af.type.ChromaDataNormalType.P1,
    )

    # threshold
    y_chroma[y_chroma < threshold] = 0

    # detect note onsets on each pitch
    notes_with_onsets = []
    for note_id in range(y_chroma.shape[0]):
        onset_env = librosa.onset.onset_strength(S=librosa.amplitude_to_db(y_chroma[note_id]), hop_length=slide_length)
        # !TBD: if possible, use ibrosa.onset.onset_backtrack on peaf_frames instead of calling whole onset_detect twice
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr, normalize=True, backtrack=True, hop_length=slide_length
        )
        peak_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr, normalize=True, backtrack=False, hop_length=slide_length
        )

        for of, pf in zip(onset_frames, peak_frames):
            notes_with_onsets.append((note_id % 12, librosa.frames_to_time(of, sr=sr), np.nan, y_chroma[note_id, pf]))

    return np.asarray(notes_with_onsets)


def extract_note_onsets_old(y, sr: float, threshold: float = 0.9):
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
    chroma = obj.chroma(obj.cqt(y), chroma_num=12, norm_type=af.type.ChromaDataNormalType.MAX)
    # chroma = obj.chroma(obj.cqt(y), chroma_num=12, norm_type=af.type.ChromaDataNormalType.P1)
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
