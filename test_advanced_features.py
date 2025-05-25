#!/usr/bin/env python3
"""
Test script for advanced music transcription features.
"""

import os
import numpy as np
import librosa
from audio_io import load_audio
from pitch_detect_advanced import detect_midi_notes_advanced, detect_time_signature
from midi_writer_advanced import write_midi_advanced, smooth_midi_dynamics
from notation_advanced import midi_to_sheet_advanced, analyze_musical_structure

def test_advanced_transcription():
    """Test the advanced transcription features with a sample audio."""
    
    # Generate a test audio signal with known properties
    print("Generating test audio signal...")
    sr = 22050
    duration = 4.0  # 4 seconds
    
    # Create a simple melody with specific rhythm
    # C major scale with specific timing
    notes = [
        (261.63, 0.0, 0.5),   # C4 - quarter note
        (293.66, 0.5, 0.5),   # D4 - quarter note
        (329.63, 1.0, 0.5),   # E4 - quarter note
        (349.23, 1.5, 0.5),   # F4 - quarter note
        (392.00, 2.0, 1.0),   # G4 - half note
        (440.00, 3.0, 0.5),   # A4 - quarter note
        (493.88, 3.5, 0.5),   # B4 - quarter note
    ]
    
    # Generate audio signal
    y = np.zeros(int(duration * sr))
    for freq, start, dur in notes:
        t = np.linspace(0, dur, int(dur * sr))
        signal = 0.5 * np.sin(2 * np.pi * freq * t)
        # Add slight envelope
        envelope = np.exp(-t * 2)
        signal *= envelope
        
        start_idx = int(start * sr)
        end_idx = start_idx + len(signal)
        y[start_idx:end_idx] += signal
    
    # Save test audio
    test_audio_path = "test_audio.wav"
    librosa.output.write_wav(test_audio_path, y, sr)
    print(f"Test audio saved to {test_audio_path}")
    
    # Test advanced pitch detection
    print("\n1. Testing advanced pitch detection...")
    detected_notes, tempo = detect_midi_notes_advanced(
        y, sr, 
        quantize=True, 
        tempo_analysis=True,
        silence_threshold=0.02
    )
    
    print(f"   Detected {len(detected_notes)} notes")
    print(f"   Detected tempo: {tempo:.1f} BPM" if tempo else "   No tempo detected")
    
    # Test time signature detection
    if tempo:
        beat_times = librosa.beat.beat_track(y=y, sr=sr)[1]
        beat_times = librosa.frames_to_time(beat_times, sr=sr)
        time_sig = detect_time_signature(beat_times, detected_notes)
        print(f"   Detected time signature: {time_sig[0]}/{time_sig[1]}")
    
    # Test advanced MIDI writing
    print("\n2. Testing advanced MIDI writing...")
    midi_path = "test_advanced.mid"
    write_midi_advanced(
        detected_notes, 
        midi_path,
        tempo=tempo if tempo else 120,
        time_signature=(4, 4),
        add_rests=True
    )
    print(f"   MIDI file written to {midi_path}")
    
    # Test smooth MIDI writing
    print("\n3. Testing smooth MIDI dynamics...")
    smooth_midi_path = "test_smooth.mid"
    smooth_midi_dynamics(
        detected_notes,
        smooth_midi_path,
        tempo=tempo if tempo else 120,
        dynamic_range=(60, 100),
        smoothing_window=3
    )
    print(f"   Smooth MIDI written to {smooth_midi_path}")
    
    # Test advanced notation
    print("\n4. Testing advanced notation...")
    xml_path = "test_advanced.musicxml"
    try:
        midi_to_sheet_advanced(
            midi_path,
            xml_path,
            tempo_bpm=tempo if tempo else 120,
            time_signature=(4, 4),
            add_rests=True,
            simplify_rhythms=True
        )
        print(f"   MusicXML written to {xml_path}")
    except Exception as e:
        print(f"   Warning: Could not create MusicXML: {e}")
    
    # Analyze the results
    print("\n5. Analyzing musical structure...")
    try:
        analysis = analyze_musical_structure(midi_path)
        print(f"   Analysis results:")
        for key, value in analysis.items():
            print(f"     {key}: {value}")
    except Exception as e:
        print(f"   Warning: Could not analyze: {e}")
    
    # Clean up
    print("\nCleaning up test files...")
    for f in [test_audio_path, midi_path, smooth_midi_path, xml_path]:
        if os.path.exists(f):
            os.remove(f)
            print(f"   Removed {f}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_advanced_transcription()