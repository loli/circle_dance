import audioflux as af
import librosa
import numpy as np
import numpy.typing as npt


class NoteEnergyCqt:

    def __init__(
        self,
        sr: float,
        filter_scale: float = 2.0,
        slide_length: int = 1024,
        padding_frames: int = 1,
        norm_type: str = "octave",
        norm_div_init: float = 5.0,
        norm_div_alpha: float = 0.002,
        low_freq=af.utils.note_to_hz("C1"),
        n_octaves: int = 7,
        n_notes_per_octave: int = 12,
    ):
        """

        Computes the Constant-Q power spectrum for subsequent chunks of audio, e.g. read from a stream.
        The results has `n_octaves * n_notes_per_octave`, bins reaching from `low_freq` up logarithmically spaced.

        Normalization is done via a running divisor, initialized with `norm_div_init` and updated each chunk with the `norm_div_alpha` part of the chunk's maximum values.
        Actual normalization is performed with `max(running_divisor, max(cqt))`. That means strong power spectrums are always max normalized.
        But a sudden energy lull does not lead immediately to boosting of potential noise. Only longer stretches of low enery chunks lead to a lowered `running_divisor`.
        Running / max norm can be computed globally, per octave, or per note.

        Since the CQT does not work well on the edges of small audio chunks, a padding by one or more frames is recommended.

        A higher (>1) `filter_scale` leads to crisper signal detection, aka single frquency bin doesn't leak that much into the adjecant bins.
        This is a very influencial parameters and should take values between 0.5 and 2. preferably.

        Args:
            sr: Sample rate of the audio.
            filter_scale: Scale factor for the filter. Named `factor` in audioflux.CQT().
            slide_length: Length of the slide for the CQT.
            padding_frames: Number of frames to pad the end of the audio.
            norm_type: norm type, one of `global`, `octave`, and `note`
            norm_div_init: Initial value for normalization divisor.
            norm_div_alpha: Alpha value for running normalization divisor update.
            low_freq: Lowest frequency to start the CQT.
            n_octaves: Number of octaves to include in the CQT.
            n_notes_per_octave: Number of notes per octave.
        """
        assert padding_frames >= 0
        assert norm_type in ["global", "octave", "note"]
        assert norm_div_init > 0
        assert norm_div_alpha >= 0
        assert n_octaves > 0
        assert n_notes_per_octave > 0

        self.sr = sr
        self.slide_length = slide_length
        self.n_padding_frames = padding_frames
        self.n_padding_samples = librosa.frames_to_samples(padding_frames, hop_length=slide_length)
        self.norm_type = norm_type
        self.running_norm_div = np.asarray([norm_div_init] * (n_octaves * n_notes_per_octave))
        self.norm_div_alpha = norm_div_alpha
        self.note_ids = np.arange(n_octaves * n_notes_per_octave)

        self.filter_scale = filter_scale
        self.low_freq = low_freq
        self.n_octaves = n_octaves
        self.n_notes_per_octave = n_notes_per_octave

    def extract(self, y: npt.NDArray, carryover_samples: int):
        """Extract the normalized Constant-Q power spectrum from an audio chunk.

        This method is specifically designed to work with short duration chunks, e.g. from an audio stream. It utilizes a running max values for normalization.

        Args:
            y: audio data

        Returns:
            the CQT power spectrum; shape=(3, N),
                with rows=(note_id, onset(sec), normed_cqt_power_spectrum[0,1])
        """
        if self.n_padding_samples > 0:
            y = np.pad(y, (0, self.n_padding_samples), mode="edge")

        cqt, _ = af.cqt(
            y,
            num=self.n_octaves * self.n_notes_per_octave,
            samplate=int(self.sr),
            low_fre=self.low_freq,
            bin_per_octave=self.n_notes_per_octave,
            slide_length=self.slide_length,
            normal_type=af.type.SpectralFilterBankNormalType.AREA,  # SpectralFilterBankNormalType.NONE | AREA | BAND_WIDTH,
            is_scale=True,
            factor=self.filter_scale,
            window_type=af.type.WindowType.HANN,
        )
        cqt = np.abs(cqt)

        if self.norm_type == "global":
            max_val = cqt.max()
        elif self.norm_type == "octave":
            max_val = cqt.max(axis=1).reshape(self.n_octaves, self.n_notes_per_octave).max(axis=1)
            max_val = np.repeat(max_val, self.n_notes_per_octave)
        elif self.norm_type == "note":
            max_val = cqt.max(axis=1)
        self.running_norm_div = (1 - self.norm_div_alpha) * self.running_norm_div + self.norm_div_alpha * max_val
        cqt = cqt / np.maximum(max_val, self.running_norm_div)[:, None]

        if self.n_padding_samples > 0:
            cqt = cqt[:, : -self.n_padding_frames]
        cqt = cqt[:, librosa.samples_to_frames(carryover_samples, hop_length=self.slide_length) :]

        return cqt

    # Note: prefers steam_reader with
    #    buffer_replenish_multiplier = 1
    #    buffer_carryover_multiplier = 4/8
    def callback(
        self,
        buffer: npt.NDArray,
        sr: float,
        stream_clock: float,
        carryover_samples: int,
        carryover_time_sec: float,
    ) -> npt.NDArray:
        power_spectrum = self.extract(
            buffer[:-1], carryover_samples
        )  # |TBD: -1 required? Otherwise returns one frame too many
        power_spectrum = power_spectrum[::-1, :]  # lower notes should be at bottom
        frame_times = librosa.frames_to_time(range(power_spectrum.shape[1]), sr=self.sr, hop_length=self.slide_length)
        frame_times += stream_clock
        duration = librosa.frames_to_time(1)
        return [(frame_times, duration, power_spectrum)]
