import pretty_midi

def write_midi_improved(notes, output_path, program=0, velocity=100):
    """
    Improved MIDI writer that uses actual note durations.
    
    :param notes: list of (start_time, duration, midi_note_number) tuples
    :param output_path: filesystem path to write the .mid file
    :param program: MIDI program (instrument) number (0 = Acoustic Grand Piano)
    :param velocity: note velocity (0-127)
    """
    # Create a new PrettyMIDI object
    pm = pretty_midi.PrettyMIDI()
    
    # Create one Instrument instance
    instrument = pretty_midi.Instrument(program=program)
    
    # Add notes with their actual durations
    for start, duration, pitch in notes:
        # Calculate end time from start + duration
        end = start + duration
        
        # Create note with actual duration
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=pitch,
            start=start,
            end=end
        )
        
        instrument.notes.append(note)
    
    # Add the instrument to the PrettyMIDI object
    pm.instruments.append(instrument)
    
    # Write out the MIDI file
    pm.write(output_path)
    print(f"[INFO] Improved MIDI written to {output_path}")
    
    # Print some statistics
    print(f"[INFO] Total notes: {len(notes)}")
    if notes:
        print(f"[INFO] Duration range: {min(n[1] for n in notes):.3f}s - {max(n[1] for n in notes):.3f}s")
        print(f"[INFO] Pitch range: {min(n[2] for n in notes)} - {max(n[2] for n in notes)}")


def write_midi_with_filtering(notes, output_path, program=0, velocity=100, 
                            min_duration=0.05, max_duration=2.0):
    """
    MIDI writer with additional filtering to remove very short or long notes.
    
    :param notes: list of (start_time, duration, midi_note_number) tuples
    :param output_path: filesystem path to write the .mid file
    :param program: MIDI program number
    :param velocity: note velocity
    :param min_duration: minimum note duration to include
    :param max_duration: maximum note duration to include
    """
    pm = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=program)
    
    filtered_notes = []
    
    for start, duration, pitch in notes:
        # Filter out notes that are too short or too long
        if min_duration <= duration <= max_duration:
            # Also filter out extreme pitches that might be errors
            if 21 <= pitch <= 108:  # Piano range: A0 to C8
                end = start + duration
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=pitch,
                    start=start,
                    end=end
                )
                instrument.notes.append(note)
                filtered_notes.append((start, duration, pitch))
    
    pm.instruments.append(instrument)
    pm.write(output_path)
    
    print(f"[INFO] Filtered MIDI written to {output_path}")
    print(f"[INFO] Kept {len(filtered_notes)} notes out of {len(notes)} total")
    print(f"[INFO] Filtered out {len(notes) - len(filtered_notes)} notes")