import numpy as np
import librosa

def detect_midi_notes_improved(y, sr, hop_length=512, mag_threshold=0.1, min_note_duration=0.05):
    """
    Improved version that reduces overlapping notes by consolidating consecutive frames
    of the same pitch into single notes.
    
    :param y: np.ndarray - Time-series audio signal (mono)
    :param sr: int - Sampling rate
    :param hop_length: int - Samples between frames
    :param mag_threshold: float - Relative magnitude threshold (0-1)
    :param min_note_duration: float - Minimum note duration in seconds
    :return: List[Tuple[float, float, int]] - List of (start_time, duration, midi_note)
    """
    
    # Get pitch and magnitude data
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)
    
    # Convert frame indices to time
    times = librosa.frames_to_time(np.arange(pitches.shape[1]), sr=sr, hop_length=hop_length)
    
    # First pass: collect all detected pitches with their times
    detected_pitches = []
    
    for frame_idx in range(pitches.shape[1]):
        mag_column = magnitudes[:, frame_idx]
        
        # Skip quiet frames
        if mag_column.max() < mag_threshold:
            detected_pitches.append(None)
            continue
            
        # Find the bin with maximum magnitude
        best_bin = mag_column.argmax()
        freq = pitches[best_bin, frame_idx]
        
        if freq > 0:
            midi_note = int(np.round(librosa.hz_to_midi(freq)))
            detected_pitches.append(midi_note)
        else:
            detected_pitches.append(None)
    
    # Second pass: consolidate consecutive identical pitches
    notes = []
    current_note = None
    note_start = None
    
    for i, pitch in enumerate(detected_pitches):
        if pitch != current_note:
            # End the previous note if it exists
            if current_note is not None and note_start is not None:
                duration = times[i-1] - note_start
                if duration >= min_note_duration:  # Only keep notes longer than minimum
                    notes.append((note_start, duration, current_note))
            
            # Start a new note
            current_note = pitch
            note_start = times[i] if pitch is not None else None
    
    # Don't forget the last note
    if current_note is not None and note_start is not None:
        duration = times[-1] - note_start
        if duration >= min_note_duration:
            notes.append((note_start, duration, current_note))
    
    return notes


def detect_midi_notes_with_onset(y, sr, hop_length=512, onset_threshold=0.3):
    """
    Alternative approach using onset detection to better segment notes.
    
    :param y: np.ndarray - Time-series audio signal
    :param sr: int - Sampling rate
    :param hop_length: int - Samples between frames
    :param onset_threshold: float - Onset detection sensitivity
    :return: List[Tuple[float, float, int]] - List of (start_time, duration, midi_note)
    """
    
    # Detect onsets (note starts)
    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr, hop_length=hop_length, backtrack=True
    )
    
    # Convert onset frames to time
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)
    
    # Get pitch information
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)
    
    notes = []
    
    # Process each onset
    for i in range(len(onset_times)):
        start_time = onset_times[i]
        
        # Determine end time (next onset or end of audio)
        if i < len(onset_times) - 1:
            end_time = onset_times[i + 1]
        else:
            end_time = len(y) / sr
        
        # Find the frames corresponding to this note
        start_frame = int(librosa.time_to_frames(start_time, sr=sr, hop_length=hop_length))
        end_frame = int(librosa.time_to_frames(end_time, sr=sr, hop_length=hop_length))
        
        # Get the most common pitch in this segment
        segment_pitches = []
        
        for frame in range(start_frame, min(end_frame, pitches.shape[1])):
            mag_column = magnitudes[:, frame]
            if mag_column.max() > 0.1:  # magnitude threshold
                best_bin = mag_column.argmax()
                freq = pitches[best_bin, frame]
                if freq > 0:
                    midi_note = int(np.round(librosa.hz_to_midi(freq)))
                    segment_pitches.append(midi_note)
        
        # Use the most common pitch in the segment
        if segment_pitches:
            # Find most common pitch (mode)
            unique, counts = np.unique(segment_pitches, return_counts=True)
            most_common_pitch = unique[np.argmax(counts)]
            
            duration = end_time - start_time
            notes.append((start_time, duration, most_common_pitch))
    
    return notes