#!/usr/bin/env python3
"""
Simple verification script to check if all modules have proper syntax.
"""

# Test imports
try:
    import pitch_detect_advanced
    print("✓ pitch_detect_advanced imports successfully")
except Exception as e:
    print(f"✗ pitch_detect_advanced error: {e}")

try:
    import midi_writer_advanced
    print("✓ midi_writer_advanced imports successfully")
except Exception as e:
    print(f"✗ midi_writer_advanced error: {e}")

try:
    import notation_advanced
    print("✓ notation_advanced imports successfully")
except Exception as e:
    print(f"✗ notation_advanced error: {e}")

# Check function signatures
print("\nFunction signatures:")
print(f"detect_midi_notes_advanced: {pitch_detect_advanced.detect_midi_notes_advanced.__doc__}")
print(f"write_midi_advanced: {midi_writer_advanced.write_midi_advanced.__doc__}")
print(f"midi_to_sheet_advanced: {notation_advanced.midi_to_sheet_advanced.__doc__}")