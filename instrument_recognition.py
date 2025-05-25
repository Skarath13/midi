"""
Instrument Recognition Module
Uses timbre features and machine learning for instrument classification
"""

import numpy as np
import librosa
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Common instrument MIDI program mappings
INSTRUMENT_PROGRAMS = {
    'piano': 0,
    'guitar': 24,
    'violin': 40,
    'trumpet': 56,
    'saxophone': 65,
    'flute': 73,
    'drums': 128  # Channel 10
}

# Instrument family groups
INSTRUMENT_FAMILIES = {
    'piano': ['acoustic_piano', 'electric_piano', 'harpsichord', 'clavinet'],
    'guitar': ['acoustic_guitar', 'electric_guitar', 'bass_guitar'],
    'strings': ['violin', 'viola', 'cello', 'contrabass'],
    'brass': ['trumpet', 'trombone', 'french_horn', 'tuba'],
    'woodwind': ['flute', 'clarinet', 'oboe', 'saxophone'],
    'percussion': ['drums', 'timpani', 'xylophone', 'vibraphone']
}

def extract_timbre_features(y, sr, hop_length=512, n_mfcc=13):
    """
    Extract timbre-related features for instrument recognition.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param hop_length: Hop length for feature extraction
    :param n_mfcc: Number of MFCC coefficients
    :return: Feature dictionary
    """
    features = {}
    
    # 1. MFCCs (Mel-frequency cepstral coefficients)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc, hop_length=hop_length)
    features['mfcc_mean'] = np.mean(mfccs, axis=1)
    features['mfcc_std'] = np.std(mfccs, axis=1)
    
    # 2. Spectral features
    # Spectral centroid (brightness)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)
    features['spectral_centroid_mean'] = np.mean(spectral_centroid)
    features['spectral_centroid_std'] = np.std(spectral_centroid)
    
    # Spectral rolloff
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length)
    features['spectral_rolloff_mean'] = np.mean(spectral_rolloff)
    features['spectral_rolloff_std'] = np.std(spectral_rolloff)
    
    # Spectral bandwidth
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop_length)
    features['spectral_bandwidth_mean'] = np.mean(spectral_bandwidth)
    features['spectral_bandwidth_std'] = np.std(spectral_bandwidth)
    
    # Spectral contrast
    spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop_length)
    features['spectral_contrast_mean'] = np.mean(spectral_contrast, axis=1)
    features['spectral_contrast_std'] = np.std(spectral_contrast, axis=1)
    
    # 3. Zero crossing rate (percussiveness)
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)
    features['zcr_mean'] = np.mean(zcr)
    features['zcr_std'] = np.std(zcr)
    
    # 4. Temporal features
    # Attack time estimation
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    
    if len(onset_frames) > 0:
        # Estimate attack time from first onset
        attack_frame = onset_frames[0]
        attack_env = onset_env[:attack_frame + 10]  # Look at 10 frames after onset
        if len(attack_env) > 1:
            attack_time = np.argmax(attack_env) * hop_length / sr
            features['attack_time'] = attack_time
        else:
            features['attack_time'] = 0.01
    else:
        features['attack_time'] = 0.01
    
    # 5. Harmonic features
    harmonic, percussive = librosa.effects.hpss(y)
    features['harmonic_ratio'] = np.sum(np.abs(harmonic)) / (np.sum(np.abs(y)) + 1e-6)
    
    # Flatten all features into a single vector
    feature_vector = []
    feature_names = []
    
    for key, value in features.items():
        if isinstance(value, np.ndarray):
            for i, v in enumerate(value):
                feature_vector.append(v)
                feature_names.append(f"{key}_{i}")
        else:
            feature_vector.append(value)
            feature_names.append(key)
    
    return np.array(feature_vector), feature_names

def create_instrument_classifier():
    """
    Create a simple instrument classifier using Random Forest.
    Note: This is a placeholder. In practice, you would train on a large dataset.
    """
    # This is a simplified example - real implementation would use a trained model
    classifier = RandomForestClassifier(n_estimators=100, random_state=42)
    scaler = StandardScaler()
    
    return classifier, scaler

def classify_instrument_simple(y, sr, segment_duration=2.0):
    """
    Simple rule-based instrument classification based on timbre features.
    This is a heuristic approach without machine learning.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param segment_duration: Duration of segment to analyze
    :return: Dictionary with instrument predictions
    """
    print("[INFO] Performing instrument recognition...")
    
    # Use first few seconds for analysis
    segment_samples = int(segment_duration * sr)
    if len(y) > segment_samples:
        y_segment = y[:segment_samples]
    else:
        y_segment = y
    
    # Extract features
    features, feature_names = extract_timbre_features(y_segment, sr)
    
    # Simple heuristic classification based on features
    predictions = {}
    
    # Get key features
    spectral_centroid_mean = features[feature_names.index('spectral_centroid_mean')]
    zcr_mean = features[feature_names.index('zcr_mean')]
    harmonic_ratio = features[feature_names.index('harmonic_ratio')]
    attack_time = features[feature_names.index('attack_time')]
    
    # Normalize spectral centroid to 0-1 range
    normalized_centroid = np.clip(spectral_centroid_mean / 4000, 0, 1)
    
    # Piano characteristics: moderate brightness, low ZCR, high harmonic
    piano_score = (1 - abs(normalized_centroid - 0.3)) * (1 - zcr_mean) * harmonic_ratio
    predictions['piano'] = piano_score
    
    # Guitar characteristics: moderate brightness, moderate ZCR
    guitar_score = (1 - abs(normalized_centroid - 0.4)) * (1 - abs(zcr_mean - 0.05))
    predictions['guitar'] = guitar_score
    
    # Violin characteristics: high brightness, high harmonic
    violin_score = normalized_centroid * harmonic_ratio * (1 - zcr_mean)
    predictions['violin'] = violin_score
    
    # Brass characteristics: very high brightness, fast attack
    brass_score = normalized_centroid * (1 - attack_time) * harmonic_ratio
    predictions['brass'] = brass_score
    
    # Woodwind characteristics: moderate-high brightness, smooth attack
    woodwind_score = (normalized_centroid * 0.7) * attack_time * harmonic_ratio
    predictions['woodwind'] = woodwind_score
    
    # Drums characteristics: high ZCR, low harmonic ratio, fast attack
    drums_score = zcr_mean * (1 - harmonic_ratio) * (1 - attack_time)
    predictions['drums'] = drums_score
    
    # Normalize scores
    total_score = sum(predictions.values()) + 1e-6
    for instrument in predictions:
        predictions[instrument] /= total_score
    
    # Get most likely instrument
    most_likely = max(predictions.items(), key=lambda x: x[1])
    
    result = {
        'instrument': most_likely[0],
        'confidence': most_likely[1],
        'all_scores': predictions,
        'features': {
            'spectral_centroid': spectral_centroid_mean,
            'zero_crossing_rate': zcr_mean,
            'harmonic_ratio': harmonic_ratio,
            'attack_time': attack_time
        }
    }
    
    print(f"[INFO] Most likely instrument: {result['instrument']} (confidence: {result['confidence']:.3f})")
    
    return result

def segment_by_instrument(y, sr, notes, segment_duration=1.0):
    """
    Attempt to separate notes by instrument based on timbre analysis.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param notes: List of detected notes
    :param segment_duration: Duration for instrument analysis
    :return: Dictionary mapping instruments to their notes
    """
    print("[INFO] Segmenting notes by instrument...")
    
    instrument_notes = {
        'piano': [],
        'guitar': [],
        'violin': [],
        'brass': [],
        'woodwind': [],
        'drums': [],
        'unknown': []
    }
    
    # Analyze timbre around each note onset
    for note in notes:
        start_time, duration, pitch = note[:3]
        start_sample = int(start_time * sr)
        end_sample = int((start_time + min(duration, segment_duration)) * sr)
        
        if start_sample < len(y) and end_sample <= len(y):
            note_segment = y[start_sample:end_sample]
            
            # Classify instrument for this segment
            if len(note_segment) > 1024:  # Minimum length for analysis
                result = classify_instrument_simple(note_segment, sr)
                instrument = result['instrument']
                confidence = result['confidence']
                
                # Add note to appropriate instrument list
                if confidence > 0.3:  # Confidence threshold
                    if instrument in instrument_notes:
                        instrument_notes[instrument].append(note + (confidence,))
                    else:
                        instrument_notes['unknown'].append(note + (0.0,))
                else:
                    instrument_notes['unknown'].append(note + (0.0,))
            else:
                instrument_notes['unknown'].append(note + (0.0,))
    
    # Print statistics
    for instrument, notes_list in instrument_notes.items():
        if notes_list:
            print(f"[INFO] {instrument}: {len(notes_list)} notes")
    
    return instrument_notes

def create_multi_instrument_midi(instrument_notes, output_path, tempo=120):
    """
    Create a MIDI file with multiple instruments.
    
    :param instrument_notes: Dictionary mapping instruments to notes
    :param output_path: Path to save MIDI file
    :param tempo: Tempo in BPM
    """
    import pretty_midi
    
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    for instrument_name, notes in instrument_notes.items():
        if notes and instrument_name != 'unknown':
            # Get MIDI program number
            if instrument_name in INSTRUMENT_PROGRAMS:
                program = INSTRUMENT_PROGRAMS[instrument_name]
            else:
                program = 0  # Default to piano
            
            # Create instrument
            is_drum = (instrument_name == 'drums')
            instrument = pretty_midi.Instrument(program=program, is_drum=is_drum)
            
            # Add notes
            for note_data in notes:
                if len(note_data) >= 3:
                    start, duration, pitch = note_data[:3]
                    velocity = note_data[3] if len(note_data) > 3 else 100
                    
                    # For drums, map to GM drum sounds
                    if is_drum:
                        # Simple mapping: use pitch to select drum sound
                        drum_map = {
                            36: 36,  # Kick
                            38: 38,  # Snare
                            42: 42,  # Hi-hat closed
                            46: 46,  # Hi-hat open
                            49: 49,  # Crash
                            51: 51,  # Ride
                        }
                        pitch = drum_map.get(pitch % 12 + 36, 38)  # Default to snare
                    
                    note = pretty_midi.Note(
                        velocity=int(velocity),
                        pitch=int(pitch),
                        start=start,
                        end=start + duration
                    )
                    instrument.notes.append(note)
            
            pm.instruments.append(instrument)
    
    pm.write(output_path)
    print(f"[INFO] Multi-instrument MIDI written to {output_path}")

def analyze_instrumentation(y, sr):
    """
    Analyze the instrumentation of an audio file.
    
    :param y: Audio signal
    :param sr: Sample rate
    :return: Dictionary with instrumentation analysis
    """
    # Overall instrument classification
    overall_result = classify_instrument_simple(y, sr, segment_duration=5.0)
    
    # Analyze different sections
    section_duration = 10.0  # 10-second sections
    section_samples = int(section_duration * sr)
    num_sections = max(1, len(y) // section_samples)
    
    section_results = []
    for i in range(num_sections):
        start = i * section_samples
        end = min((i + 1) * section_samples, len(y))
        section = y[start:end]
        
        if len(section) > 1024:
            result = classify_instrument_simple(section, sr)
            section_results.append({
                'start_time': start / sr,
                'instrument': result['instrument'],
                'confidence': result['confidence']
            })
    
    return {
        'primary_instrument': overall_result['instrument'],
        'confidence': overall_result['confidence'],
        'all_scores': overall_result['all_scores'],
        'timbre_features': overall_result['features'],
        'sections': section_results
    }