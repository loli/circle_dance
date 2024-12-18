import audioflux as af
import librosa
import numpy as np
import scipy


def extract_note_durations(y, sr: float, thr: float = 0.9, slide_length: int = 512):
    """Extract from an audio chunk all notes/sounds with chroma energy above the threshold and returns their duration
    and energy.

    Note:
        This does not detect note onsets, just the duration of a certain chroma in the chromagram.

    Note:
        slide_length in audioflux = hop_length in librosa

    Args:
        y: audio data
        sr: sampling rate of the audio data
        thr: the chroma energy threshold for considering a note as active; between 0 and 1
        slide_length: the slide length used to compute the chromagram

    Returns:
        the detect N notes and their duration; shape=(N, 4),
            with columns=(note_id, onset(sec), conclusion(sec), mean_chroma_energy[0,1])
    """
    # calculate chromagram
    obj = af.CQT(
        num=12 * 7,
        samplate=int(sr),
        low_fre=af.utils.note_to_hz("C1"),
        bin_per_octave=12,
        slide_length=slide_length,
        # is_scale=False,
        # thresh=0.5,
    )
    # chromagram = obj.chroma(obj.cqt(y), chroma_num=12)  # , norm_type=af.type.ChromaDataNormalType.NONE)
    chromagram = obj.chroma(obj.cqt(y), chroma_num=12, norm_type=af.type.ChromaDataNormalType.P1)

    # prepare
    chrom_bin_time_delta = slide_length / sr
    structure_element = np.asarray([[False, False, False], [True, True, True], [False, False, False]])
    n_chromas, n_chroma_bins = chromagram.shape

    # convert chroma bins to their start times (in sec)
    chroms_bin_start_times = librosa.frames_to_time(range(n_chroma_bins), sr=sr, hop_length=slide_length)

    # binary morphology magic, applied on each row separately, due to 1D structure element
    chroma_thr = chromagram > thr
    start_and_end = chroma_thr ^ scipy.ndimage.binary_erosion(chroma_thr, structure=structure_element)
    labels, label_count = scipy.ndimage.label(chroma_thr, structure=structure_element)

    if label_count == 0:
        return np.empty((0, 4))

    # extract start and end of each detected stucture
    labels_start_end = labels[start_and_end]
    times_start_end = np.tile(chroms_bin_start_times, (n_chromas, 1))[start_and_end]

    # pair and deal with fact that we can have single-element structures in the buffer
    # can work on whole chroma array at once, as each row has unique labels
    i = 0
    durations = []
    while i < len(labels_start_end):
        if i + 1 < len(labels_start_end) and labels_start_end[i] == labels_start_end[i + 1]:  # double label
            durations.append((times_start_end[i], times_start_end[i + 1]))
            i += 2
        else:  # single label
            durations.append((times_start_end[i], times_start_end[i]))
            i += 1
    durations_arr = np.asarray(durations)
    durations_arr[:, 1] += chrom_bin_time_delta  # add chroma bin time to end, as bin time denotes bin start

    # extract node id's and mean chroma energies
    note_ids = []
    chroma_energies = []
    for lid in range(label_count):
        lmask = labels == (lid + 1)
        note_ids.append(np.where(lmask)[0][0])
        chroma_energies.append(chromagram[lmask].mean())

    # note that time ranges for entries of the same note never overlap
    return np.hstack([np.asarray(note_ids).reshape(-1, 1), durations_arr, np.asarray(chroma_energies).reshape(-1, 1)])
