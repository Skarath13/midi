# pitch_detect.py
import numpy as np
import librosa

def detect_midi_notes(y, sr, hop_length=512, mag_threshold=0.1):
    """
    Detect pitches in the audio and convert to MIDI note numbers.
    :param y: waveform array
    :param sr: sample rate
    :param hop_length: hop length for STFT/piptrack
    :param mag_threshold: ignore magnitudes below this (relative)
    :return: list of (time_sec, midi_note) tuples
    """
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)
    times = librosa.frames_to_time(np.arange(pitches.shape[1]), sr=sr,
                                   hop_length=hop_length)

    notes = []
    for i in range(pitches.shape[1]):
        mag = magnitudes[:, i]
        if mag.max() < mag_threshold:
            continue
        index = mag.argmax()
        freq = pitches[index, i]
        if freq > 0:
            midi = int(np.round(librosa.hz_to_midi(freq)))
            notes.append((times[i], midi))
    return notes