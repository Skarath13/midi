# Music Transcription Improvements

## Overview of the Application

This is a web-based music transcription tool that converts audio files (WAV, MP3, FLAC) into MIDI and sheet music notation. The application uses pitch detection algorithms to analyze audio and generate musical notation that can be downloaded and edited in music software.

## Original Issues

The original implementation had a significant problem that caused MIDI files to sound "glitchy" or like the music was skipping:

1. **Fixed Note Duration**: Every detected note was assigned a fixed duration of 0.4 seconds, regardless of how long the note actually lasted in the audio.

2. **Frame Overlap**: The pitch detection runs on every frame (every ~23ms with hop_length=512), creating hundreds of overlapping MIDI notes for what should be a single sustained note.

3. **No Note Segmentation**: The algorithm had no way to determine when one note ends and another begins, creating a continuous stream of overlapping notes.

## Solutions Implemented

### 1. Improved Pitch Detection (`pitch_detect_improved.py`)

**Method 1: Consolidation Approach**
- Groups consecutive frames with the same pitch into single notes
- Calculates actual note duration based on how long a pitch is sustained
- Filters out very short notes (< 50ms) that are likely artifacts

**Method 2: Onset Detection Approach**
- Uses librosa's onset detection to find where notes begin
- Segments audio between onsets to determine note boundaries
- Selects the most common pitch within each segment

### 2. Enhanced MIDI Writer (`midi_writer_improved.py`)

- Uses actual note durations instead of fixed 0.4s
- Provides filtering options to remove outliers
- Adds statistics reporting for debugging

### 3. Updated Web Interface

- Added method selection (Improved/Onset/Filtered)
- Shows transcription statistics
- Clear indication of improvements made

## How to Use the Improvements

### Testing Different Methods

Run the test script to compare all methods:
```bash
python test_improved.py
```

This generates four MIDI files:
- `output_original.mid` - Original glitchy version
- `output_improved.mid` - Consolidated pitch approach
- `output_onset.mid` - Onset-based segmentation
- `output_filtered.mid` - Filtered version

### Using the Improved Web App

```bash
python app_improved.py
```

Then visit http://localhost:5001 and try different transcription methods.

## Technical Details

### Key Parameters

- **hop_length**: 512 samples (~23ms at 22050 Hz)
- **mag_threshold**: 0.1 (minimum magnitude to consider)
- **min_note_duration**: 0.05s (50ms minimum note length)
- **Filtering ranges**: 0.1-1.5s duration, MIDI notes 21-108 (piano range)

### Performance Comparison

Original method on a 10-second audio file:
- Generates ~400-500 overlapping notes
- Results in stuttering/glitchy playback

Improved consolidation method:
- Generates ~20-50 notes (depending on content)
- Smooth, natural playback

Onset-based method:
- Best for percussive/rhythmic content
- May miss gradual pitch changes

## Future Improvements

1. **Polyphonic Transcription**: Current implementation only detects one pitch per frame
2. **Dynamic Velocity**: All notes currently have fixed velocity (100)
3. **Tempo Detection**: Could analyze rhythm patterns
4. **Key Signature Detection**: Help with accidental notation
5. **Real-time Processing**: Stream processing for live audio

## Summary

The main issue was that the original code created a new MIDI note for every analysis frame, resulting in hundreds of overlapping 0.4-second notes. The improved version properly segments the audio into distinct notes with appropriate durations, resulting in clean, musical MIDI output.