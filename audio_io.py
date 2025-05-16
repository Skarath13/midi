# audio_io.py
import librosa
import librosa.display
import matplotlib.pyplot as plt

def load_audio(path, sr=None):
    """
    Load an audio file.
    :param path: path to .wav (or other) audio file
    :param sr: target sampling rate (None to preserve original)
    :return: tuple (y, sr) where y is waveform array, sr is sample rate
    """
    y, sr = librosa.load(path, sr=sr)
    return y, sr

def plot_waveform(y, sr, figsize=(10, 3), title="Waveform"):
    """
    Plot the audio waveform.
    :param y: waveform array
    :param sr: sample rate
    """
    plt.figure(figsize=figsize)
    librosa.display.waveshow(y, sr=sr)
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    plt.show()