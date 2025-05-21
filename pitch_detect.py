import numpy as np
import librosa

def detect_midi_notes(y, sr, hop_length=512, mag_threshold=0.1):
    """
    Analyze an audio waveform and extract a sequence of MIDI note events.

    :param y: np.ndarray
        Time-series audio signal (mono) as a 1D NumPy array.
    :param sr: int
        Sampling rate of the audio (samples per second).
    :param hop_length: int, optional
        Number of samples between successive frames for STFT/pitch tracking.
        Higher hop_length → lower time resolution but faster computation.
    :param mag_threshold: float, optional
        Relative magnitude threshold (0–1) to ignore low-energy frames.
        Frames whose max magnitude < mag_threshold are skipped.
    :return: List[Tuple[float, int]]
        List of (time_in_seconds, midi_note_number) tuples for each detected pitch.
    """

    # librosa.piptrack returns two 2D arrays:
    #   pitches.shape = (n_bins, n_frames)  and  magnitudes.shape = (n_bins, n_frames)
    # Each column i represents the STFT frame at time frame i.
    pitches, magnitudes = librosa.piptrack(
        y=y,
        sr=sr,
        hop_length=hop_length
    )

    # Convert frame indices to time stamps in seconds
    # np.arange(pitches.shape[1]) generates [0, 1, 2, ..., n_frames-1]
    times = librosa.frames_to_time(
        np.arange(pitches.shape[1]),
        sr=sr,
        hop_length=hop_length
    )

    notes = []  # Will hold the (time, midi_note) pairs

    # Loop over each time frame
    for frame_idx in range(pitches.shape[1]):
        mag_column = magnitudes[:, frame_idx]

        # Skip frames where the loudest bin is below our threshold
        if mag_column.max() < mag_threshold:
            continue

        # Find the index of the bin with maximum magnitude
        best_bin = mag_column.argmax()
        freq = pitches[best_bin, frame_idx]  # Frequency in Hz

        # Only consider positive, non-zero frequencies
        if freq > 0:
            # Convert Hz to a MIDI note number (float → nearest int)
            midi_note = int(np.round(librosa.hz_to_midi(freq)))
            notes.append((times[frame_idx], midi_note))

    return notes