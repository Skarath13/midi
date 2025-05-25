"""
Key Signature and Chord Detection Module
Implements algorithms for detecting musical key and chord progressions
"""

import numpy as np
import librosa
from scipy.stats import pearsonr
from collections import Counter
import pretty_midi

# Krumhansl-Schmuckler key profiles
# Major and minor profiles based on probe tone experiments
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

# Chord templates (relative to root)
CHORD_TEMPLATES = {
    'major': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    'minor': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
    'diminished': [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
    'augmented': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    'major7': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
    'minor7': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    'dominant7': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
}

# Note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def extract_chroma_features(y, sr, hop_length=512, n_fft=2048):
    """
    Extract chroma features from audio.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param hop_length: Hop length for STFT
    :param n_fft: FFT size
    :return: Chroma features (12 x time_frames)
    """
    # Use CQT-based chroma for better results
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    
    # Normalize to ensure each frame sums to 1
    chroma_norm = librosa.util.normalize(chroma, axis=0, norm=1)
    
    return chroma_norm

def detect_key_krumhansl(chroma_vector):
    """
    Detect key using Krumhansl-Schmuckler algorithm.
    
    :param chroma_vector: 12-dimensional chroma vector (averaged over time)
    :return: Tuple of (key_name, mode, correlation_coefficient)
    """
    correlations = []
    
    # Test all 24 possible keys (12 major + 12 minor)
    for shift in range(12):
        # Rotate chroma vector
        rotated_chroma = np.roll(chroma_vector, shift)
        
        # Correlate with major profile
        major_corr, _ = pearsonr(rotated_chroma, MAJOR_PROFILE)
        correlations.append((NOTE_NAMES[shift], 'major', major_corr))
        
        # Correlate with minor profile
        minor_corr, _ = pearsonr(rotated_chroma, MINOR_PROFILE)
        correlations.append((NOTE_NAMES[shift], 'minor', minor_corr))
    
    # Find best match
    best_match = max(correlations, key=lambda x: x[2])
    
    return best_match

def detect_key_signature(y, sr, hop_length=512):
    """
    Detect the key signature of an audio file.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param hop_length: Hop length for analysis
    :return: Dictionary with key information
    """
    print("[INFO] Detecting key signature...")
    
    # Extract chroma features
    chroma = extract_chroma_features(y, sr, hop_length=hop_length)
    
    # Average over time to get global chroma vector
    mean_chroma = np.mean(chroma, axis=1)
    
    # Detect key using Krumhansl-Schmuckler
    key_name, mode, confidence = detect_key_krumhansl(mean_chroma)
    
    # Also compute key using windowed approach for confidence
    window_size = int(5 * sr / hop_length)  # 5-second windows
    stride = window_size // 2
    
    windowed_keys = []
    for i in range(0, chroma.shape[1] - window_size, stride):
        window_chroma = np.mean(chroma[:, i:i+window_size], axis=1)
        win_key, win_mode, _ = detect_key_krumhansl(window_chroma)
        windowed_keys.append(f"{win_key} {win_mode}")
    
    # Most common key from windows
    if windowed_keys:
        key_counter = Counter(windowed_keys)
        most_common_key = key_counter.most_common(1)[0]
        consistency = most_common_key[1] / len(windowed_keys)
    else:
        consistency = 1.0
    
    result = {
        'key': key_name,
        'mode': mode,
        'confidence': confidence,
        'consistency': consistency,
        'full_name': f"{key_name} {mode}"
    }
    
    print(f"[INFO] Detected key: {result['full_name']} (confidence: {confidence:.3f}, consistency: {consistency:.3f})")
    
    return result

def detect_chord(chroma_frame, threshold=0.6):
    """
    Detect chord from a single chroma frame.
    
    :param chroma_frame: 12-dimensional chroma vector
    :param threshold: Correlation threshold for chord detection
    :return: Tuple of (root_note, chord_type, confidence)
    """
    best_match = None
    best_correlation = -1
    
    # Normalize chroma
    if np.sum(chroma_frame) > 0:
        chroma_norm = chroma_frame / np.sum(chroma_frame)
    else:
        return None, None, 0
    
    # Test each possible root note
    for root in range(12):
        rotated_chroma = np.roll(chroma_norm, -root)
        
        # Test each chord type
        for chord_type, template in CHORD_TEMPLATES.items():
            # Compute correlation
            correlation = np.dot(rotated_chroma, template) / np.sqrt(
                np.dot(template, template) * np.dot(rotated_chroma, rotated_chroma)
            )
            
            if correlation > best_correlation:
                best_correlation = correlation
                best_match = (NOTE_NAMES[root], chord_type, correlation)
    
    # Return chord if above threshold
    if best_correlation >= threshold:
        return best_match
    else:
        return None, None, 0

def detect_chord_progression(y, sr, hop_length=512, segment_time=0.5):
    """
    Detect chord progression from audio.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param hop_length: Hop length for analysis
    :param segment_time: Time per chord segment in seconds
    :return: List of (time, chord_name, confidence) tuples
    """
    print("[INFO] Detecting chord progression...")
    
    # Extract chroma features
    chroma = extract_chroma_features(y, sr, hop_length=hop_length)
    
    # Time array
    times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop_length)
    
    # Segment size in frames
    segment_frames = int(segment_time * sr / hop_length)
    
    chord_progression = []
    
    # Process each segment
    for i in range(0, chroma.shape[1], segment_frames):
        segment_chroma = chroma[:, i:i+segment_frames]
        
        if segment_chroma.shape[1] > 0:
            # Average chroma over segment
            mean_segment_chroma = np.mean(segment_chroma, axis=1)
            
            # Detect chord
            root, chord_type, confidence = detect_chord(mean_segment_chroma)
            
            if root is not None:
                chord_name = f"{root}{'' if chord_type == 'major' else chord_type}"
                chord_progression.append((times[i], chord_name, confidence))
    
    # Post-process: smooth progression
    smoothed_progression = []
    if chord_progression:
        current_chord = chord_progression[0]
        chord_start = current_chord[0]
        
        for i in range(1, len(chord_progression)):
            if chord_progression[i][1] != current_chord[1]:
                # Chord changed
                duration = chord_progression[i][0] - chord_start
                smoothed_progression.append((chord_start, duration, current_chord[1], current_chord[2]))
                current_chord = chord_progression[i]
                chord_start = current_chord[0]
        
        # Add last chord
        duration = times[-1] - chord_start
        smoothed_progression.append((chord_start, duration, current_chord[1], current_chord[2]))
    
    print(f"[INFO] Detected {len(smoothed_progression)} chord changes")
    
    return smoothed_progression

def create_chord_midi(chord_progression, output_path, tempo=120):
    """
    Create a MIDI file from chord progression.
    
    :param chord_progression: List of (start_time, duration, chord_name, confidence) tuples
    :param output_path: Path to save MIDI file
    :param tempo: Tempo in BPM
    """
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # Piano for chords
    piano = pretty_midi.Instrument(program=0)
    
    for start, duration, chord_name, confidence in chord_progression:
        # Parse chord name
        if len(chord_name) > 1 and chord_name[1] == '#':
            root_name = chord_name[:2]
            chord_type = chord_name[2:] if len(chord_name) > 2 else 'major'
        else:
            root_name = chord_name[0]
            chord_type = chord_name[1:] if len(chord_name) > 1 else 'major'
        
        # Get root MIDI number
        try:
            root_idx = NOTE_NAMES.index(root_name)
            root_midi = 60 + root_idx  # Middle C octave
        except ValueError:
            continue
        
        # Get chord intervals
        if chord_type == '' or chord_type == 'major':
            intervals = [0, 4, 7]  # Major triad
        elif chord_type == 'minor' or chord_type == 'm':
            intervals = [0, 3, 7]  # Minor triad
        elif chord_type == 'diminished' or chord_type == 'dim':
            intervals = [0, 3, 6]  # Diminished triad
        elif chord_type == 'augmented' or chord_type == 'aug':
            intervals = [0, 4, 8]  # Augmented triad
        elif chord_type == 'major7' or chord_type == 'maj7':
            intervals = [0, 4, 7, 11]  # Major 7th
        elif chord_type == 'minor7' or chord_type == 'm7':
            intervals = [0, 3, 7, 10]  # Minor 7th
        elif chord_type == 'dominant7' or chord_type == '7':
            intervals = [0, 4, 7, 10]  # Dominant 7th
        else:
            intervals = [0, 4, 7]  # Default to major
        
        # Create chord notes
        velocity = int(confidence * 100)  # Scale confidence to velocity
        for interval in intervals:
            note = pretty_midi.Note(
                velocity=velocity,
                pitch=root_midi + interval,
                start=start,
                end=start + duration
            )
            piano.notes.append(note)
    
    pm.instruments.append(piano)
    pm.write(output_path)
    
    print(f"[INFO] Chord progression MIDI written to {output_path}")

def analyze_harmonic_structure(y, sr):
    """
    Comprehensive harmonic analysis of audio.
    
    :param y: Audio signal
    :param sr: Sample rate
    :return: Dictionary with key and chord information
    """
    # Detect key signature
    key_info = detect_key_signature(y, sr)
    
    # Detect chord progression
    chord_progression = detect_chord_progression(y, sr)
    
    # Analyze chord statistics
    chord_counts = Counter([chord[2] for chord in chord_progression])
    most_common_chords = chord_counts.most_common(5)
    
    # Calculate tonal stability (how well chords fit the key)
    key_root = NOTE_NAMES.index(key_info['key'])
    in_key_chords = 0
    
    for _, _, chord_name, _ in chord_progression:
        chord_root = chord_name[0]
        if chord_root in NOTE_NAMES:
            chord_root_idx = NOTE_NAMES.index(chord_root)
            # Check if chord root is in key (simplified)
            if chord_root_idx in [key_root, (key_root + 2) % 12, (key_root + 4) % 12,
                                 (key_root + 5) % 12, (key_root + 7) % 12, (key_root + 9) % 12,
                                 (key_root + 11) % 12]:
                in_key_chords += 1
    
    tonal_stability = in_key_chords / len(chord_progression) if chord_progression else 0
    
    return {
        'key': key_info,
        'chord_progression': chord_progression,
        'most_common_chords': most_common_chords,
        'tonal_stability': tonal_stability,
        'total_chords': len(chord_progression)
    }