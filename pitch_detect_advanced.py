import numpy as np
import librosa
from scipy.signal import medfilt
from collections import Counter

def harmonic_product_spectrum(spectrum, sr, num_harmonics=5):
    """
    Apply harmonic product spectrum to better detect fundamental frequency
    even when the fundamental is weak or missing.
    
    :param spectrum: Magnitude spectrum
    :param sr: Sample rate
    :param num_harmonics: Number of harmonics to consider
    :return: HPS spectrum
    """
    hps = spectrum.copy()
    for h in range(2, min(num_harmonics + 1, len(spectrum) // 2)):
        decimated = spectrum[::h]
        hps[:len(decimated)] *= decimated
    return hps

def detect_tempo_and_beats(y, sr):
    """
    Detect tempo and beat positions in the audio using onset strength.
    Following best practices from Ellis's dynamic programming method.
    """
    # Calculate onset strength with median aggregation for better results
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
    
    # Use onset envelope for more accurate beat tracking
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    
    return tempo, beat_times, onset_env

def quantize_to_grid(time, beat_times, subdivisions=4):
    """
    Quantize a time value to the nearest beat grid position.
    
    :param time: Time value to quantize
    :param beat_times: Array of beat times
    :param subdivisions: Number of subdivisions per beat (4 = 16th notes)
    :return: Quantized time
    """
    if len(beat_times) < 2:
        return time
    
    # Calculate average beat duration
    beat_duration = np.mean(np.diff(beat_times))
    subdivision_duration = beat_duration / subdivisions
    
    # Find nearest beat
    nearest_beat_idx = np.argmin(np.abs(beat_times - time))
    nearest_beat = beat_times[nearest_beat_idx]
    
    # Calculate offset from nearest beat
    offset = time - nearest_beat
    
    # Quantize to nearest subdivision
    subdivision_number = round(offset / subdivision_duration)
    quantized_time = nearest_beat + subdivision_number * subdivision_duration
    
    return max(0, quantized_time)

def detect_midi_notes_advanced(y, sr, hop_length=512, mag_threshold=0.1, 
                              min_note_duration=0.05, quantize=True,
                              tempo_analysis=True, silence_threshold=0.02):
    """
    Advanced pitch detection with rhythm quantization and rest detection.
    
    :param y: Audio signal
    :param sr: Sample rate
    :param hop_length: Hop length for pitch detection
    :param mag_threshold: Magnitude threshold for pitch detection
    :param min_note_duration: Minimum note duration in seconds
    :param quantize: Whether to quantize note timings
    :param tempo_analysis: Whether to perform tempo analysis
    :param silence_threshold: Threshold for detecting silence (rests)
    :return: List of (start_time, duration, midi_note) tuples
    """
    
    # Detect tempo and beats if requested
    tempo = None
    beat_times = None
    onset_env = None
    if tempo_analysis:
        try:
            tempo, beat_times, onset_env = detect_tempo_and_beats(y, sr)
            print(f"[INFO] Detected tempo: {tempo:.1f} BPM")
        except:
            print("[WARNING] Tempo detection failed, continuing without quantization")
            quantize = False
    
    # Apply window function for cleaner frequency analysis (best practice)
    # Using Hann window as recommended for pitch detection
    window = np.hanning(hop_length * 2)
    
    # Get pitch and magnitude data
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length, 
                                         win_length=hop_length * 2, 
                                         window=window)
    
    # Apply median filter to smooth pitch detection
    for i in range(pitches.shape[1]):
        if magnitudes[:, i].max() > 0:
            magnitudes[:, i] = medfilt(magnitudes[:, i], kernel_size=5)
    
    # Convert frame indices to time
    times = librosa.frames_to_time(np.arange(pitches.shape[1]), sr=sr, hop_length=hop_length)
    
    # Get RMS energy for silence detection
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    
    # First pass: collect all detected pitches with their times
    detected_pitches = []
    pitch_confidences = []
    
    for frame_idx in range(pitches.shape[1]):
        mag_column = magnitudes[:, frame_idx]
        
        # Check for silence
        if rms[frame_idx] < silence_threshold:
            detected_pitches.append(None)
            pitch_confidences.append(0)
            continue
        
        # Skip quiet frames
        if mag_column.max() < mag_threshold:
            detected_pitches.append(None)
            pitch_confidences.append(0)
            continue
            
        # Find the bin with maximum magnitude
        best_bin = mag_column.argmax()
        freq = pitches[best_bin, frame_idx]
        
        if freq > 0:
            midi_note = int(np.round(librosa.hz_to_midi(freq)))
            # Confidence based on magnitude relative to threshold
            confidence = mag_column.max() / mag_threshold
            detected_pitches.append(midi_note)
            pitch_confidences.append(confidence)
        else:
            detected_pitches.append(None)
            pitch_confidences.append(0)
    
    # Second pass: consolidate consecutive identical pitches with smoothing
    notes = []
    current_note = None
    note_start = None
    note_confidences = []
    
    for i, pitch in enumerate(detected_pitches):
        # Check if we should continue the current note
        should_continue = False
        if current_note is not None and pitch is not None:
            # Allow small pitch variations (within 1 semitone)
            if abs(pitch - current_note) <= 1:
                should_continue = True
        
        if pitch != current_note and not should_continue:
            # End the previous note if it exists
            if current_note is not None and note_start is not None:
                # Use median pitch for stability
                if note_confidences:
                    # Weight by confidence
                    pitch_values = [p for p, c in note_confidences if p is not None]
                    confidence_values = [c for p, c in note_confidences if p is not None]
                    
                    if pitch_values:
                        # Weighted median
                        sorted_pairs = sorted(zip(pitch_values, confidence_values), 
                                            key=lambda x: x[0])
                        cumsum = np.cumsum([c for _, c in sorted_pairs])
                        median_idx = np.searchsorted(cumsum, cumsum[-1] / 2)
                        final_pitch = sorted_pairs[median_idx][0]
                    else:
                        final_pitch = current_note
                else:
                    final_pitch = current_note
                
                duration = times[i-1] - note_start
                if duration >= min_note_duration:
                    # Quantize if enabled
                    if quantize and beat_times is not None:
                        quantized_start = quantize_to_grid(note_start, beat_times)
                        quantized_end = quantize_to_grid(note_start + duration, beat_times)
                        quantized_duration = quantized_end - quantized_start
                        notes.append((quantized_start, quantized_duration, final_pitch))
                    else:
                        notes.append((note_start, duration, final_pitch))
            
            # Start a new note
            current_note = pitch
            note_start = times[i] if pitch is not None else None
            note_confidences = [(pitch, pitch_confidences[i])] if pitch is not None else []
        elif should_continue and pitch is not None:
            # Add to current note's pitch history
            note_confidences.append((pitch, pitch_confidences[i]))
    
    # Don't forget the last note
    if current_note is not None and note_start is not None:
        duration = times[-1] - note_start
        if duration >= min_note_duration:
            if quantize and beat_times is not None:
                quantized_start = quantize_to_grid(note_start, beat_times)
                quantized_end = quantize_to_grid(note_start + duration, beat_times)
                quantized_duration = quantized_end - quantized_start
                notes.append((quantized_start, quantized_duration, current_note))
            else:
                notes.append((note_start, duration, current_note))
    
    # Sort notes by start time
    notes.sort(key=lambda x: x[0])
    
    # Post-process to remove overlaps
    cleaned_notes = []
    for i, (start, duration, pitch) in enumerate(notes):
        if i > 0:
            prev_start, prev_duration, prev_pitch = cleaned_notes[-1]
            prev_end = prev_start + prev_duration
            
            # If this note starts before the previous ends, trim the previous
            if start < prev_end:
                new_duration = start - prev_start
                cleaned_notes[-1] = (prev_start, new_duration, prev_pitch)
        
        cleaned_notes.append((start, duration, pitch))
    
    return cleaned_notes, tempo

def detect_downbeats(beat_times, onset_env, beats, beats_per_measure=4):
    """
    Detect downbeats by finding which beat offset has the highest energy.
    
    :param beat_times: Array of beat times
    :param onset_env: Onset strength envelope
    :param beats: Beat frame indices
    :param beats_per_measure: Number of beats per measure
    :return: Downbeat offset (0-indexed)
    """
    if len(beats) < beats_per_measure:
        return 0
    
    # Calculate energy at each beat position modulo beats_per_measure
    beat_energies = []
    for beat_frame in beats:
        if beat_frame < len(onset_env):
            beat_energies.append(onset_env[beat_frame])
    
    if not beat_energies:
        return 0
    
    # Sum energies for each possible downbeat offset
    downbeat_candidates = []
    for offset in range(min(beats_per_measure, len(beat_energies))):
        energy_sum = sum(beat_energies[offset::beats_per_measure])
        downbeat_candidates.append((offset, energy_sum))
    
    # Return offset with highest energy
    best_offset = max(downbeat_candidates, key=lambda x: x[1])[0]
    return best_offset

def detect_time_signature(beat_times, notes, onset_env=None, beats=None):
    """
    Attempt to detect the time signature from beat times and notes.
    Enhanced with downbeat detection for better accuracy.
    
    :param beat_times: Array of beat times
    :param notes: List of (start, duration, pitch) tuples
    :param onset_env: Optional onset strength envelope for downbeat detection
    :param beats: Optional beat frame indices
    :return: Tuple of (numerator, denominator) for time signature
    """
    if len(beat_times) < 4:
        return 4, 4  # Default to 4/4
    
    # Calculate beat durations
    beat_durations = np.diff(beat_times)
    avg_beat_duration = np.mean(beat_durations)
    
    # Detect downbeats if onset envelope is provided
    downbeat_offset = 0
    if onset_env is not None and beats is not None:
        # Try different beat groupings
        for beats_per_measure in [3, 4, 6]:
            offset = detect_downbeats(beat_times, onset_env, beats, beats_per_measure)
            if offset == 0:  # Strong first beat suggests correct grouping
                if beats_per_measure == 3:
                    return 3, 4
                elif beats_per_measure == 6:
                    return 6, 8
    
    # Look for patterns in note onsets relative to beats
    note_starts = [n[0] for n in notes]
    
    # Count notes per measure (assuming 4 beats per measure initially)
    measures = []
    measure_start = 0
    
    for i in range(4, len(beat_times), 4):
        measure_end = beat_times[i] if i < len(beat_times) else beat_times[-1]
        
        # Count notes in this measure
        notes_in_measure = sum(1 for start in note_starts 
                             if measure_start <= start < measure_end)
        measures.append(notes_in_measure)
        measure_start = measure_end
    
    if not measures:
        return 4, 4
    
    # Most common number of notes per measure might indicate time signature
    common_counts = Counter(measures).most_common(3)
    
    # Simple heuristics for common time signatures
    if common_counts[0][0] <= 3:
        return 3, 4  # Waltz time
    elif common_counts[0][0] >= 6:
        return 6, 8  # Compound time
    else:
        return 4, 4  # Common time