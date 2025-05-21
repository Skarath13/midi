# midi_writer.py

import pretty_midi  # library for creating and manipulating MIDI data

def write_midi(notes, output_path, program=0, default_duration=0.4, velocity=100):
    """
    Build a MIDI file from a list of detected notes.
    
    :param notes: list of (start_time, midi_note_number) tuples
    :param output_path: filesystem path to write the .mid file
    :param program: MIDI program (instrument) number (0 = Acoustic Grand Piano)
    :param default_duration: how long each note lasts (in seconds) if no duration info
    :param velocity: note velocity (0–127), i.e. how “loud” each note is
    """
    # Create a new PrettyMIDI object, which will contain all tracks/instruments
    pm = pretty_midi.PrettyMIDI()
    
    # Create one Instrument instance (MIDI track) using the given program number
    instrument = pretty_midi.Instrument(program=program)

    # Loop over each detected pitch event
    for start, pitch in notes:
        # Set an end time for each note by adding default_duration to its start time
        end = start + default_duration
        
        # Create a Note object with the given velocity, MIDI pitch number,
        # and the computed start/end times
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=pitch,
            start=start,
            end=end
        )
        
        # Add this note to our instrument’s note list
        instrument.notes.append(note)

    # After populating all notes, add the instrument track to the PrettyMIDI container
    pm.instruments.append(instrument)

    # Write out the assembled MIDI data to the specified file path
    pm.write(output_path)
    print(f"[INFO] MIDI written to {output_path}")