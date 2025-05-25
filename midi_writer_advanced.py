import pretty_midi
import numpy as np

def create_time_signature_changes(tempo, numerator=4, denominator=4):
    """
    Create time signature change events for MIDI.
    
    :param tempo: Tempo in BPM
    :param numerator: Time signature numerator
    :param denominator: Time signature denominator
    :return: List of time signature changes
    """
    time_sig = pretty_midi.TimeSignature(numerator, denominator, 0)
    return [time_sig]

def write_midi_advanced(notes, output_path, tempo=None, time_signature=(4, 4),
                       program=0, velocity=100, add_rests=True):
    """
    Advanced MIDI writer with tempo, time signature, and rest handling.
    
    :param notes: List of (start_time, duration, midi_note) tuples
    :param output_path: Path to write MIDI file
    :param tempo: Tempo in BPM (if None, uses 120 BPM)
    :param time_signature: Tuple of (numerator, denominator)
    :param program: MIDI program number
    :param velocity: Note velocity
    :param add_rests: Whether to add explicit rests
    """
    # Create PrettyMIDI object with tempo
    if tempo is None:
        tempo = 120.0
    
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # Add time signature
    time_sig = pretty_midi.TimeSignature(time_signature[0], time_signature[1], 0)
    pm.time_signature_changes = [time_sig]
    
    # Create instrument
    instrument = pretty_midi.Instrument(program=program)
    
    # Calculate measure duration
    beats_per_measure = time_signature[0]
    beat_duration = 60.0 / tempo  # Duration of one beat in seconds
    measure_duration = beats_per_measure * beat_duration
    
    # Sort notes by start time
    sorted_notes = sorted(notes, key=lambda x: x[0])
    
    # Prevent overlapping notes (best practice from research)
    cleaned_notes = []
    for i, (start, duration, pitch) in enumerate(sorted_notes):
        if i > 0 and cleaned_notes:
            prev_start, prev_duration, prev_pitch = cleaned_notes[-1]
            prev_end = prev_start + prev_duration
            
            # If this note starts before the previous ends, trim the previous
            if start < prev_end:
                new_duration = max(0.05, start - prev_start)  # Minimum 50ms
                cleaned_notes[-1] = (prev_start, new_duration, prev_pitch)
        
        cleaned_notes.append((start, duration, pitch))
    
    sorted_notes = cleaned_notes
    
    # Add notes with velocity scaling based on position in measure
    for i, (start, duration, pitch) in enumerate(sorted_notes):
        # Calculate position within measure
        measure_position = (start % measure_duration) / measure_duration
        
        # Slightly accent downbeats
        if measure_position < 0.1:  # Near start of measure
            note_velocity = min(127, int(velocity * 1.1))
        else:
            note_velocity = velocity
        
        # Create note
        end = start + duration
        
        # Ensure minimum note length for better playback
        if duration < 0.05:
            end = start + 0.05
        
        note = pretty_midi.Note(
            velocity=note_velocity,
            pitch=pitch,
            start=start,
            end=end
        )
        instrument.notes.append(note)
    
    # Add instrument to MIDI
    pm.instruments.append(instrument)
    
    # If requested, add a percussion track to mark beats
    if add_rests and tempo is not None:
        # Create a subtle metronome track
        percussion = pretty_midi.Instrument(program=0, is_drum=True)
        
        # Add subtle hi-hat on beats
        beat_times = np.arange(0, pm.get_end_time(), beat_duration)
        for i, beat_time in enumerate(beat_times):
            # Accent downbeats
            if i % beats_per_measure == 0:
                # Kick drum on downbeat
                note = pretty_midi.Note(
                    velocity=40,
                    pitch=36,  # Kick drum
                    start=beat_time,
                    end=beat_time + 0.1
                )
                percussion.notes.append(note)
            else:
                # Hi-hat on other beats
                note = pretty_midi.Note(
                    velocity=20,
                    pitch=42,  # Closed hi-hat
                    start=beat_time,
                    end=beat_time + 0.05
                )
                percussion.notes.append(note)
        
        # Only add percussion if it doesn't interfere too much
        if len(percussion.notes) < len(instrument.notes) * 2:
            pm.instruments.append(percussion)
    
    # Write MIDI file
    pm.write(output_path)
    
    # Print statistics
    print(f"[INFO] Advanced MIDI written to {output_path}")
    print(f"[INFO] Tempo: {tempo:.1f} BPM")
    print(f"[INFO] Time Signature: {time_signature[0]}/{time_signature[1]}")
    print(f"[INFO] Total notes: {len(notes)}")
    
    if notes:
        # Calculate some rhythm statistics
        note_starts = [n[0] for n in sorted_notes]
        if len(note_starts) > 1:
            intervals = np.diff(note_starts)
            print(f"[INFO] Average note interval: {np.mean(intervals):.3f}s")
            print(f"[INFO] Most common interval: {np.median(intervals):.3f}s")

def smooth_midi_dynamics(notes, output_path, tempo=None, program=0,
                        dynamic_range=(60, 100), smoothing_window=5):
    """
    Write MIDI with smoothed dynamics to reduce audio bumps.
    
    :param notes: List of (start_time, duration, midi_note) tuples
    :param output_path: Path to write MIDI file
    :param tempo: Tempo in BPM
    :param program: MIDI program number
    :param dynamic_range: Tuple of (min_velocity, max_velocity)
    :param smoothing_window: Window size for velocity smoothing
    """
    if tempo is None:
        tempo = 120.0
    
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    instrument = pretty_midi.Instrument(program=program)
    
    # Sort notes by start time
    sorted_notes = sorted(notes, key=lambda x: x[0])
    
    # Calculate velocities based on note density and pitch
    velocities = []
    for i, (start, duration, pitch) in enumerate(sorted_notes):
        # Base velocity on pitch (higher notes slightly quieter)
        pitch_factor = 1.0 - (pitch - 60) / 60.0  # Normalize around middle C
        pitch_factor = np.clip(pitch_factor, 0.7, 1.3)
        
        # Check note density in surrounding area
        window_start = max(0, i - smoothing_window // 2)
        window_end = min(len(sorted_notes), i + smoothing_window // 2 + 1)
        
        # Count notes in window
        window_notes = sorted_notes[window_start:window_end]
        density = len(window_notes) / (smoothing_window + 1)
        
        # Reduce velocity in dense sections
        density_factor = 1.0 / (1.0 + density * 0.2)
        
        # Calculate velocity
        base_velocity = (dynamic_range[0] + dynamic_range[1]) / 2
        velocity = int(base_velocity * pitch_factor * density_factor)
        velocity = np.clip(velocity, dynamic_range[0], dynamic_range[1])
        velocities.append(velocity)
    
    # Smooth velocities
    if len(velocities) > smoothing_window:
        # Apply moving average
        smoothed_velocities = []
        for i in range(len(velocities)):
            window_start = max(0, i - smoothing_window // 2)
            window_end = min(len(velocities), i + smoothing_window // 2 + 1)
            avg_velocity = int(np.mean(velocities[window_start:window_end]))
            smoothed_velocities.append(avg_velocity)
        velocities = smoothed_velocities
    
    # Create notes with smoothed velocities
    for i, (start, duration, pitch) in enumerate(sorted_notes):
        # Add small fade in/out to reduce clicks
        note_velocity = velocities[i]
        
        # For very short notes, reduce velocity to minimize clicks
        if duration < 0.1:
            note_velocity = int(note_velocity * 0.8)
        
        note = pretty_midi.Note(
            velocity=note_velocity,
            pitch=pitch,
            start=start,
            end=start + duration
        )
        instrument.notes.append(note)
    
    pm.instruments.append(instrument)
    pm.write(output_path)
    
    print(f"[INFO] Smoothed MIDI written to {output_path}")
    print(f"[INFO] Velocity range: {min(velocities)} - {max(velocities)}")