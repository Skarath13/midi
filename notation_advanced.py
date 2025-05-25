from music21 import converter, stream, tempo, meter, note, rest, environment
from music21.duration import Duration
import numpy as np

def quantize_duration(duration_seconds, tempo_bpm=120, allowed_durations=None):
    """
    Quantize a duration in seconds to the nearest musical duration.
    
    :param duration_seconds: Duration in seconds
    :param tempo_bpm: Tempo in BPM
    :param allowed_durations: List of allowed durations (e.g., [4, 2, 1, 0.5, 0.25])
    :return: Quantized duration as music21 duration type
    """
    if allowed_durations is None:
        # Common note durations: whole, half, quarter, eighth, sixteenth
        allowed_durations = [4, 2, 1, 0.5, 0.25]
    
    # Convert seconds to quarter note durations
    beat_duration = 60.0 / tempo_bpm  # Duration of one beat in seconds
    duration_quarters = duration_seconds / beat_duration
    
    # Find closest allowed duration
    closest_duration = min(allowed_durations, 
                          key=lambda x: abs(x - duration_quarters))
    
    return closest_duration

def midi_to_sheet_advanced(midi_path, xml_output, png_output=None, 
                          musescore_path=None, tempo_bpm=None,
                          time_signature=None, add_rests=True,
                          simplify_rhythms=True):
    """
    Advanced MIDI to sheet music conversion with better musical structure.
    
    :param midi_path: Path to MIDI file
    :param xml_output: Path for MusicXML output
    :param png_output: Optional path for PNG output
    :param musescore_path: Path to MuseScore executable
    :param tempo_bpm: Override tempo (if None, uses MIDI tempo)
    :param time_signature: Override time signature as tuple (num, denom)
    :param add_rests: Whether to add rests between notes
    :param simplify_rhythms: Whether to simplify complex rhythms
    """
    # Configure MuseScore if provided
    if musescore_path:
        us = environment.UserSettings()
        us['musescoreDirectPNGPath'] = musescore_path
    
    # Parse MIDI file
    score = converter.parse(midi_path)
    
    # Create a new score with proper structure
    new_score = stream.Score()
    part = stream.Part()
    
    # Extract notes from original score
    all_notes = []
    for element in score.flatten():
        if isinstance(element, note.Note):
            all_notes.append({
                'pitch': element.pitch,
                'start': element.offset,
                'duration': element.duration.quarterLength,
                'velocity': element.volume.velocity if element.volume.velocity else 64
            })
    
    # Sort by start time
    all_notes.sort(key=lambda x: x['start'])
    
    # Detect or set tempo
    if tempo_bpm is None:
        # Try to get tempo from MIDI
        tempo_marks = list(score.flatten().getElementsByClass(tempo.MetronomeMark))
        if tempo_marks:
            tempo_bpm = tempo_marks[0].number
        else:
            tempo_bpm = 120.0
    
    # Create first measure to hold tempo and time signature (best practice)
    first_measure = stream.Measure(number=1)
    
    # Add tempo marking to first measure
    tempo_mark = tempo.MetronomeMark(number=tempo_bpm)
    first_measure.insert(0, tempo_mark)
    
    # Set time signature
    if time_signature is None:
        # Try to detect from MIDI
        time_sigs = list(score.flatten().getElementsByClass(meter.TimeSignature))
        if time_sigs:
            ts = time_sigs[0]
            time_signature = (ts.numerator, ts.denominator)
        else:
            time_signature = (4, 4)
    
    # Add time signature to first measure
    ts = meter.TimeSignature(f"{time_signature[0]}/{time_signature[1]}")
    first_measure.insert(0, ts)
    
    # Add first measure to part
    part.append(first_measure)
    
    # Calculate measure duration
    measure_duration = time_signature[0] * (4.0 / time_signature[1])
    
    # Create measures with notes and rests
    current_offset = 0.0
    measure_num = 1  # Start at 1 since we already created measure 1
    
    # Group notes by measure
    measures = []
    current_measure = []
    measure_start = 0.0
    
    for note_data in all_notes:
        while note_data['start'] >= measure_start + measure_duration:
            measures.append(current_measure)
            current_measure = []
            measure_start += measure_duration
        current_measure.append(note_data)
    
    if current_measure:
        measures.append(current_measure)
    
    # Process each measure (skip first empty measure if no notes start at 0)
    for measure_idx, measure_notes in enumerate(measures):
        measure_start = measure_idx * measure_duration
        
        # Skip creating measure if it's the first one and empty (we already have measure 1)
        if measure_idx == 0 and not measure_notes:
            continue
        
        # Add rests at the beginning of measure if needed
        if measure_notes and add_rests:
            first_note_start = measure_notes[0]['start']
            rest_duration = first_note_start - measure_start
            
            if rest_duration > 0.0625:  # Minimum rest duration (64th note)
                if simplify_rhythms:
                    rest_duration = quantize_duration(rest_duration * 60.0 / tempo_bpm, 
                                                    tempo_bpm)
                r = rest.Rest(quarterLength=rest_duration)
                part.append(r)
                current_offset += rest_duration
        
        # Process notes in measure
        for i, note_data in enumerate(measure_notes):
            # Create note
            n = note.Note(note_data['pitch'])
            
            # Quantize duration if requested
            if simplify_rhythms:
                duration_seconds = note_data['duration'] * 60.0 / tempo_bpm
                n.duration.quarterLength = quantize_duration(duration_seconds, tempo_bpm)
            else:
                n.duration.quarterLength = note_data['duration']
            
            # Set velocity/dynamics
            n.volume.velocity = note_data['velocity']
            
            # Add dynamics marking for first note of measure
            if i == 0:
                if note_data['velocity'] < 40:
                    n.dynamic = 'pp'
                elif note_data['velocity'] < 55:
                    n.dynamic = 'p'
                elif note_data['velocity'] < 70:
                    n.dynamic = 'mp'
                elif note_data['velocity'] < 85:
                    n.dynamic = 'mf'
                elif note_data['velocity'] < 100:
                    n.dynamic = 'f'
                else:
                    n.dynamic = 'ff'
            
            part.append(n)
            current_offset = note_data['start'] + n.duration.quarterLength
            
            # Add rest after note if there's a gap
            if add_rests and i < len(measure_notes) - 1:
                next_start = measure_notes[i + 1]['start']
                gap = next_start - current_offset
                
                if gap > 0.0625:  # Minimum rest duration
                    if simplify_rhythms:
                        gap = quantize_duration(gap * 60.0 / tempo_bpm, tempo_bpm)
                    r = rest.Rest(quarterLength=gap)
                    part.append(r)
                    current_offset += gap
        
        # Fill rest of measure with rests if needed
        if add_rests:
            measure_end = measure_start + measure_duration
            remaining = measure_end - current_offset
            
            if remaining > 0.0625 and measure_idx < len(measures) - 1:
                if simplify_rhythms:
                    remaining = quantize_duration(remaining * 60.0 / tempo_bpm, tempo_bpm)
                r = rest.Rest(quarterLength=remaining)
                part.append(r)
                current_offset = measure_end
    
    # Add part to score
    new_score.append(part)
    
    # Clean up the score
    new_score.makeNotation(inPlace=True)
    
    # Write MusicXML
    new_score.write('musicxml', fp=xml_output)
    print(f"[INFO] Advanced MusicXML written to {xml_output}")
    
    # Generate PNG if requested
    if png_output:
        try:
            # Try to generate PNG
            new_score.write('musicxml.png', fp=png_output)
            print(f"[INFO] PNG score written to {png_output}")
        except Exception as e:
            print(f"[WARNING] Could not generate PNG: {e}")
            # Try alternative method
            try:
                import shutil
                img = new_score.write('musicxml.png')
                if img and img != png_output:
                    shutil.move(img, png_output)
                    print(f"[INFO] PNG score written to {png_output}")
            except:
                pass

def analyze_musical_structure(midi_path):
    """
    Analyze the musical structure of a MIDI file.
    
    :param midi_path: Path to MIDI file
    :return: Dictionary with analysis results
    """
    score = converter.parse(midi_path)
    
    analysis = {
        'tempo': 120,
        'time_signature': (4, 4),
        'key': 'C major',
        'total_measures': 0,
        'note_count': 0,
        'pitch_range': (0, 0),
        'average_note_duration': 0
    }
    
    # Extract tempo
    tempo_marks = list(score.flatten().getElementsByClass(tempo.MetronomeMark))
    if tempo_marks:
        analysis['tempo'] = tempo_marks[0].number
    
    # Extract time signature
    time_sigs = list(score.flatten().getElementsByClass(meter.TimeSignature))
    if time_sigs:
        ts = time_sigs[0]
        analysis['time_signature'] = (ts.numerator, ts.denominator)
    
    # Analyze notes
    notes = list(score.flatten().getElementsByClass(note.Note))
    if notes:
        analysis['note_count'] = len(notes)
        pitches = [n.pitch.midi for n in notes]
        analysis['pitch_range'] = (min(pitches), max(pitches))
        durations = [n.duration.quarterLength for n in notes]
        analysis['average_note_duration'] = np.mean(durations)
    
    # Estimate measures
    total_duration = score.flatten().highestTime
    measure_duration = analysis['time_signature'][0] * (4.0 / analysis['time_signature'][1])
    analysis['total_measures'] = int(np.ceil(total_duration / measure_duration))
    
    # Try to detect key
    try:
        key = score.analyze('key')
        analysis['key'] = str(key)
    except:
        pass
    
    return analysis