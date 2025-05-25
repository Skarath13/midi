"""
Polyphonic Music Transcription Module
Supports multiple simultaneous notes using advanced algorithms
"""

import numpy as np
import librosa
from scipy.signal import find_peaks
from collections import defaultdict
import pretty_midi

def compute_harmonic_product_spectrum(spectrum, num_harmonics=5, f_min=80, f_max=2000):
    """
    Compute harmonic product spectrum for better fundamental frequency detection.
    
    :param spectrum: Magnitude spectrum
    :param num_harmonics: Number of harmonics to consider
    :param f_min: Minimum frequency to consider (Hz)
    :param f_max: Maximum frequency to consider (Hz)
    :return: HPS spectrum
    """
    hps = spectrum.copy()
    
    for h in range(2, num_harmonics + 1):
        # Downsample spectrum by factor h
        decimated = np.zeros_like(hps)
        decimated[::h] = spectrum[::h][:len(decimated[::h])]
        hps *= decimated
    
    return hps

def extract_multi_pitch_salience(y, sr, hop_length=512, n_fft=2048, num_harmonics=5):
    """
    Extract multi-pitch salience representation using harmonic summation.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param hop_length: Hop length for STFT
    :param n_fft: FFT size
    :param num_harmonics: Number of harmonics to sum
    :return: Multi-pitch salience matrix
    """
    # Compute STFT
    D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    magnitude = np.abs(D)
    
    # Frequency bins
    frequencies = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    
    # MIDI pitch range (21 to 108 - piano range)
    midi_pitches = np.arange(21, 109)
    pitch_frequencies = librosa.midi_to_hz(midi_pitches)
    
    # Initialize salience matrix
    salience = np.zeros((len(midi_pitches), magnitude.shape[1]))
    
    # For each frame
    for frame_idx in range(magnitude.shape[1]):
        frame_magnitude = magnitude[:, frame_idx]
        
        # Apply harmonic product spectrum
        hps = compute_harmonic_product_spectrum(frame_magnitude, num_harmonics)
        
        # For each candidate pitch
        for pitch_idx, f0 in enumerate(pitch_frequencies):
            if f0 < frequencies[-1]:  # Within frequency range
                # Sum energy at fundamental and harmonics
                harmonic_sum = 0
                for h in range(1, num_harmonics + 1):
                    harmonic_freq = f0 * h
                    if harmonic_freq < frequencies[-1]:
                        # Find closest frequency bin
                        bin_idx = np.argmin(np.abs(frequencies - harmonic_freq))
                        # Weight by harmonic number (lower harmonics more important)
                        harmonic_sum += hps[bin_idx] / h
                
                salience[pitch_idx, frame_idx] = harmonic_sum
    
    return salience, midi_pitches

def detect_polyphonic_notes(salience, midi_pitches, hop_length, sr, 
                          threshold=0.3, min_duration=0.05,
                          max_polyphony=6):
    """
    Detect multiple simultaneous notes from salience representation.
    
    :param salience: Multi-pitch salience matrix
    :param midi_pitches: Array of MIDI pitch values
    :param hop_length: Hop length used in analysis
    :param sr: Sample rate
    :param threshold: Relative threshold for peak detection
    :param min_duration: Minimum note duration in seconds
    :param max_polyphony: Maximum number of simultaneous notes
    :return: List of (start_time, duration, pitch, velocity) tuples
    """
    # Time array
    times = librosa.frames_to_time(np.arange(salience.shape[1]), sr=sr, hop_length=hop_length)
    
    # Normalize salience per frame
    max_salience = np.max(salience, axis=0, keepdims=True)
    max_salience[max_salience == 0] = 1
    normalized_salience = salience / max_salience
    
    # Track active notes
    active_notes = defaultdict(lambda: {'start': None, 'frames': []})
    detected_notes = []
    
    # Process each frame
    for frame_idx in range(salience.shape[1]):
        frame_salience = normalized_salience[:, frame_idx]
        
        # Find peaks (potential notes)
        peaks, properties = find_peaks(frame_salience, 
                                     height=threshold,
                                     distance=3)  # Minimum 3 semitones apart
        
        # Sort by salience and take top N
        if len(peaks) > 0:
            peak_heights = properties['peak_heights']
            sorted_indices = np.argsort(peak_heights)[::-1][:max_polyphony]
            current_pitches = set(midi_pitches[peaks[sorted_indices]])
        else:
            current_pitches = set()
        
        # Update active notes
        all_pitches = set(active_notes.keys()) | current_pitches
        
        for pitch in all_pitches:
            if pitch in current_pitches:
                # Note is active
                if active_notes[pitch]['start'] is None:
                    active_notes[pitch]['start'] = times[frame_idx]
                active_notes[pitch]['frames'].append(frame_idx)
            else:
                # Note is not active
                if active_notes[pitch]['start'] is not None:
                    # Note has ended
                    start = active_notes[pitch]['start']
                    duration = times[frame_idx] - start
                    
                    if duration >= min_duration:
                        # Calculate average salience as velocity
                        pitch_idx = np.where(midi_pitches == pitch)[0][0]
                        avg_salience = np.mean([normalized_salience[pitch_idx, f] 
                                              for f in active_notes[pitch]['frames']])
                        velocity = int(np.clip(avg_salience * 127, 20, 127))
                        
                        detected_notes.append((start, duration, int(pitch), velocity))
                    
                    # Reset note tracking
                    active_notes[pitch] = {'start': None, 'frames': []}
    
    # Handle notes that extend to the end
    for pitch, note_info in active_notes.items():
        if note_info['start'] is not None:
            start = note_info['start']
            duration = times[-1] - start
            
            if duration >= min_duration:
                pitch_idx = np.where(midi_pitches == pitch)[0][0]
                avg_salience = np.mean([normalized_salience[pitch_idx, f] 
                                      for f in note_info['frames']])
                velocity = int(np.clip(avg_salience * 127, 20, 127))
                
                detected_notes.append((start, duration, int(pitch), velocity))
    
    # Sort by start time
    detected_notes.sort(key=lambda x: x[0])
    
    return detected_notes

def transcribe_polyphonic(y, sr, hop_length=512, n_fft=2048,
                         threshold=0.3, min_duration=0.05,
                         max_polyphony=6):
    """
    Main function for polyphonic transcription.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param hop_length: Hop length for analysis
    :param n_fft: FFT size
    :param threshold: Detection threshold
    :param min_duration: Minimum note duration
    :param max_polyphony: Maximum simultaneous notes
    :return: List of (start_time, duration, pitch, velocity) tuples
    """
    print("[INFO] Starting polyphonic transcription...")
    
    # Extract multi-pitch salience
    salience, midi_pitches = extract_multi_pitch_salience(
        y, sr, hop_length=hop_length, n_fft=n_fft
    )
    
    # Detect notes
    notes = detect_polyphonic_notes(
        salience, midi_pitches, hop_length, sr,
        threshold=threshold, min_duration=min_duration,
        max_polyphony=max_polyphony
    )
    
    print(f"[INFO] Detected {len(notes)} notes (polyphonic)")
    
    # Count simultaneous notes
    time_points = sorted(set([n[0] for n in notes] + [n[0] + n[1] for n in notes]))
    max_simultaneous = 0
    
    for t in time_points:
        simultaneous = sum(1 for n in notes if n[0] <= t < n[0] + n[1])
        max_simultaneous = max(max_simultaneous, simultaneous)
    
    print(f"[INFO] Maximum polyphony: {max_simultaneous} simultaneous notes")
    
    return notes

def write_polyphonic_midi(notes, output_path, tempo=120, program=0):
    """
    Write polyphonic notes to MIDI file.
    
    :param notes: List of (start_time, duration, pitch, velocity) tuples
    :param output_path: Path to save MIDI file
    :param tempo: Tempo in BPM
    :param program: MIDI program number
    """
    # Create PrettyMIDI object
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # Create instrument
    instrument = pretty_midi.Instrument(program=program)
    
    # Add notes
    for start, duration, pitch, velocity in notes:
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=pitch,
            start=start,
            end=start + duration
        )
        instrument.notes.append(note)
    
    # Add instrument to MIDI
    pm.instruments.append(instrument)
    
    # Write file
    pm.write(output_path)
    
    print(f"[INFO] Polyphonic MIDI written to {output_path}")
    
    # Print statistics
    pitch_counts = defaultdict(int)
    for _, _, pitch, _ in notes:
        pitch_counts[pitch] += 1
    
    print(f"[INFO] Pitch distribution: {len(pitch_counts)} unique pitches")
    most_common = sorted(pitch_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"[INFO] Most common pitches: {most_common}")