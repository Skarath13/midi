# midi_writer.py
import pretty_midi

def write_midi(notes, output_path, program=0, default_duration=0.4, velocity=100):
    """
    Build a MIDI file from a list of detected notes.
    :param notes: list of (start_time, midi_note_number)
    :param output_path: path to write .mid file
    :param program: MIDI program number (0 = Acoustic Grand Piano)
    :param default_duration: default note length in seconds
    :param velocity: MIDI velocity (0–127)
    """
    pm = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=program)

    for start, pitch in notes:
        end = start + default_duration
        note = pretty_midi.Note(velocity=velocity, pitch=pitch,
                                start=start, end=end)
        instrument.notes.append(note)

    pm.instruments.append(instrument)
    pm.write(output_path)
    print(f"[INFO] MIDI written to {output_path}")