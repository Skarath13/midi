#!/usr/bin/env python3
"""
Test script for all future enhancement features:
- Polyphonic transcription
- Key signature detection
- Chord recognition
- Instrument recognition
- Real-time audio processing
- MIDI controller input
"""

import os
import numpy as np
import librosa
from audio_io import load_audio

def test_polyphonic_transcription():
    """Test polyphonic transcription feature."""
    print("\n" + "="*50)
    print("Testing Polyphonic Transcription")
    print("="*50)
    
    # Generate test signal with multiple simultaneous notes
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(duration * sr))
    
    # C major chord (C4, E4, G4)
    frequencies = [261.63, 329.63, 392.00]
    y = np.zeros_like(t)
    
    for freq in frequencies:
        y += 0.3 * np.sin(2 * np.pi * freq * t)
    
    # Test polyphonic transcription
    from polyphonic_transcription import transcribe_polyphonic, write_polyphonic_midi
    
    notes = transcribe_polyphonic(y, sr, max_polyphony=6)
    print(f"Detected {len(notes)} notes")
    
    # Check if we detected multiple simultaneous notes
    simultaneous_notes = []
    for i, note1 in enumerate(notes):
        for j, note2 in enumerate(notes[i+1:], i+1):
            if (note1[0] <= note2[0] < note1[0] + note1[1] or
                note2[0] <= note1[0] < note2[0] + note2[1]):
                simultaneous_notes.append((note1[2], note2[2]))
    
    print(f"Found {len(simultaneous_notes)} pairs of simultaneous notes")
    
    # Save test MIDI
    write_polyphonic_midi(notes, "test_polyphonic.mid")
    print("✓ Polyphonic transcription test completed")

def test_key_chord_detection():
    """Test key signature and chord detection."""
    print("\n" + "="*50)
    print("Testing Key Signature and Chord Detection")
    print("="*50)
    
    # Generate test signal in C major with chord progression
    sr = 22050
    duration = 8.0
    
    # C-Am-F-G chord progression
    chord_sequence = [
        ([261.63, 329.63, 392.00], 2.0),  # C major
        ([220.00, 261.63, 329.63], 2.0),  # A minor
        ([174.61, 220.00, 261.63], 2.0),  # F major
        ([196.00, 246.94, 293.66], 2.0),  # G major
    ]
    
    y = np.array([])
    for frequencies, chord_duration in chord_sequence:
        t = np.linspace(0, chord_duration, int(chord_duration * sr))
        chord_signal = np.zeros_like(t)
        
        for freq in frequencies:
            chord_signal += 0.3 * np.sin(2 * np.pi * freq * t)
        
        y = np.concatenate([y, chord_signal])
    
    # Test key detection
    from key_chord_detection import detect_key_signature, detect_chord_progression, analyze_harmonic_structure
    
    key_result = detect_key_signature(y, sr)
    print(f"Detected key: {key_result['key']} {key_result['mode']} "
          f"(confidence: {key_result['confidence']:.3f})")
    
    # Test chord progression detection
    chord_progression = detect_chord_progression(y, sr)
    print(f"Detected {len(chord_progression)} chord changes")
    
    for start, duration, chord, confidence in chord_progression[:5]:
        print(f"  {start:.2f}s: {chord} (confidence: {confidence:.2f})")
    
    # Test full harmonic analysis
    harmonic_analysis = analyze_harmonic_structure(y, sr)
    print(f"Tonal stability: {harmonic_analysis['tonal_stability']:.2f}")
    
    print("✓ Key and chord detection test completed")

def test_instrument_recognition():
    """Test instrument recognition."""
    print("\n" + "="*50)
    print("Testing Instrument Recognition")
    print("="*50)
    
    # Generate synthetic instrument-like sounds
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(duration * sr))
    
    # Simulate different instruments with different timbres
    # Piano-like: strong harmonics, moderate attack
    freq = 440  # A4
    piano_like = (np.sin(2 * np.pi * freq * t) + 
                  0.5 * np.sin(2 * np.pi * freq * 2 * t) +
                  0.3 * np.sin(2 * np.pi * freq * 3 * t))
    piano_like *= np.exp(-t * 0.5)  # Decay envelope
    
    # Test instrument recognition
    from instrument_recognition import analyze_instrumentation, classify_instrument_simple
    
    instrument_result = classify_instrument_simple(piano_like, sr)
    print(f"Detected instrument: {instrument_result['instrument']} "
          f"(confidence: {instrument_result['confidence']:.3f})")
    
    print("Timbre features:")
    for feature, value in instrument_result['features'].items():
        print(f"  {feature}: {value:.3f}")
    
    # Test full instrumentation analysis
    full_analysis = analyze_instrumentation(piano_like, sr)
    print(f"Primary instrument: {full_analysis['primary_instrument']}")
    
    print("✓ Instrument recognition test completed")

def test_realtime_processing():
    """Test real-time audio processing (without actual audio input)."""
    print("\n" + "="*50)
    print("Testing Real-time Audio Processing")
    print("="*50)
    
    from realtime_audio import RealtimeTranscriber
    
    # Test initialization
    transcriber = RealtimeTranscriber(transcription_mode='monophonic')
    print("✓ Real-time transcriber initialized")
    
    # Test processing functions with synthetic data
    test_buffer = np.random.randn(4096) * 0.1
    
    # Test monophonic processing
    transcriber.process_monophonic(test_buffer)
    print("✓ Monophonic processing tested")
    
    # Test polyphonic processing
    transcriber.transcription_mode = 'polyphonic'
    transcriber.process_polyphonic(test_buffer)
    print("✓ Polyphonic processing tested")
    
    # Test chord processing
    transcriber.process_chord(test_buffer)
    print("✓ Chord processing tested")
    
    print("✓ Real-time processing test completed")

def test_midi_controller():
    """Test MIDI controller functionality."""
    print("\n" + "="*50)
    print("Testing MIDI Controller Input")
    print("="*50)
    
    from midi_controller import MIDIController
    
    # Test initialization
    controller = MIDIController()
    
    # List available ports
    ports = controller.list_available_ports()
    print(f"Found {len(ports)} MIDI ports")
    
    # Test MIDI message processing
    import mido
    
    # Simulate some MIDI messages
    test_messages = [
        mido.Message('note_on', note=60, velocity=64, channel=0),
        mido.Message('note_on', note=64, velocity=80, channel=0),
        mido.Message('note_off', note=60, velocity=0, channel=0),
        mido.Message('control_change', control=1, value=64, channel=0),
    ]
    
    for msg in test_messages:
        controller.process_midi_message(msg)
    
    print(f"Active notes: {controller.get_active_notes()}")
    print(f"Modulation value: {controller.get_control_value(1)}")
    
    print("✓ MIDI controller test completed")

def run_all_tests():
    """Run all feature tests."""
    print("\n" + "="*70)
    print("TESTING ALL FUTURE ENHANCEMENT FEATURES")
    print("="*70)
    
    try:
        test_polyphonic_transcription()
    except Exception as e:
        print(f"✗ Polyphonic transcription test failed: {e}")
    
    try:
        test_key_chord_detection()
    except Exception as e:
        print(f"✗ Key/chord detection test failed: {e}")
    
    try:
        test_instrument_recognition()
    except Exception as e:
        print(f"✗ Instrument recognition test failed: {e}")
    
    try:
        test_realtime_processing()
    except Exception as e:
        print(f"✗ Real-time processing test failed: {e}")
    
    try:
        test_midi_controller()
    except Exception as e:
        print(f"✗ MIDI controller test failed: {e}")
    
    # Clean up test files
    print("\nCleaning up test files...")
    test_files = ["test_polyphonic.mid"]
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)
            print(f"  Removed {f}")
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)

if __name__ == "__main__":
    run_all_tests()