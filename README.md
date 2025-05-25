# Advanced Music Transcription Tool

A sophisticated web-based application that automatically transcribes audio files into MIDI and sheet music notation with advanced rhythm detection, tempo analysis, and musical structure recognition. This enhanced fork includes significant improvements for accurate music transcription.

## 🎵 What's New in This Fork

### Version 3.0 - Future Features Release

**Revolutionary New Capabilities:**
- 🎹 **Polyphonic Transcription**: Detect multiple simultaneous notes and chords
- 🎼 **Key Signature Detection**: Automatic detection of musical key using Krumhansl-Schmuckler algorithm
- 🎵 **Chord Recognition**: Real-time chord progression analysis
- 🎺 **Instrument Recognition**: AI-powered instrument classification
- 🎤 **Real-time Transcription**: Live audio input with instant note detection
- 🎮 **MIDI Controller Support**: Connect MIDI keyboards and controllers

### Version 2.0 Features

**Major Enhancements:**
- Fixed rhythm and timing issues with beat-aligned quantization
- Added rest detection for proper musical phrasing
- Implemented measure organization with time signatures
- Eliminated audio playback clicks and pops
- Beautiful new Ghibli-inspired user interface

### Advanced Transcription Modes
- **🎵 Advanced Mode**: Full rhythm quantization with tempo detection, time signature analysis, and rest insertion
- **🌊 Smooth Mode**: Enhanced playback with dynamic smoothing to eliminate audio artifacts
- **🎹 Polyphonic Mode**: Transcribe multiple simultaneous notes (chords, harmonies)
- **🎼 Harmonic Mode**: Analyze key signatures and chord progressions
- **✨ Improved Mode**: Enhanced pitch detection with note consolidation
- **🥁 Onset-based Mode**: Rhythm-focused transcription using onset detection
- **🎯 Filtered Mode**: Cleaner output with duration filtering

### Core Improvements
- **Tempo Detection**: Automatic BPM detection using beat tracking algorithms
- **Rhythm Quantization**: Aligns notes to musical grid (16th note resolution)
- **Rest Detection**: Identifies silence and inserts appropriate rests
- **Time Signature Recognition**: Supports 3/4, 4/4, and 6/8 time signatures
- **Measure Organization**: Proper barline placement and measure grouping
- **Dynamic Smoothing**: Eliminates clicks and pops in MIDI playback
- **Beautiful Ghibli-inspired UI**: Whimsical, animated interface

## Features

- **Audio Format Support**: WAV, MP3, and FLAC files
- **Advanced Pitch Detection**: Multiple algorithms including harmonic analysis
- **Professional MIDI Generation**: With tempo, dynamics, and articulation
- **Sheet Music Export**: MusicXML with proper notation, rests, and measures
- **Web Interface**: Intuitive Flask-based interface with real-time feedback
- **Multiple Transcription Methods**: Choose the best approach for your music

## How It Works

1. **Audio Analysis**: Advanced pitch detection using multiple techniques:
   - Fundamental frequency estimation with `librosa.piptrack()`
   - Onset detection for rhythm analysis
   - Beat tracking for tempo detection
   - RMS energy analysis for rest identification

2. **Musical Structure Recognition**:
   - Tempo detection using dynamic programming beat tracking
   - Time signature analysis through downbeat detection
   - Rhythm quantization to musical grid
   - Rest insertion at appropriate positions

3. **MIDI Generation**: Professional-quality MIDI creation:
   - Tempo and time signature metadata
   - Dynamic velocity based on musical context
   - Note overlap prevention
   - Optional metronome track

4. **Sheet Music Export**: MusicXML generation with:
   - Proper measure organization
   - Tempo and time signature markings
   - Dynamic markings (pp, p, mp, mf, f, ff)
   - Rest notation between notes

## Installation

### Option 1: Clone the Enhanced Fork (Recommended)

1. Clone this enhanced repository:
```bash
git clone https://github.com/Skarath13/midi.git
cd midi
```

### Option 2: Upgrade from Original Repository

If you have the original repository, you can add this fork as a remote:
```bash
# Add the enhanced fork as a remote
git remote add enhanced https://github.com/Skarath13/midi.git

# Fetch and merge the improvements
git fetch enhanced
git merge enhanced/main
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set MuseScore path for sheet music rendering:
```bash
# macOS/Linux
export MUSESCORE_PATH=/usr/bin/mscore

# Windows PowerShell
setx MUSESCORE_PATH "C:\Program Files\MuseScore 3\bin\mscore.exe"
```

## Usage

### Web Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser to `http://localhost:8001`

3. Choose your transcription method:
   - **🎵 Advanced**: Best for sheet music with proper rhythm and rests
   - **🌊 Smooth**: Best for MIDI playback without artifacts
   - **🎹 Polyphonic**: For music with multiple simultaneous notes
   - **🎼 Harmonic**: Analyze key signatures and chord progressions
   - **✨ Improved**: Good general-purpose transcription
   - **🥁 Onset-based**: Best for rhythmic/percussive music
   - **🎯 Filtered**: Cleanest output with filtered notes

4. Upload an audio file (WAV, MP3, or FLAC)

5. Click "Transcribe the Magic ✨"

6. Download:
   - **MIDI file**: For use in any DAW or music software
   - **MusicXML**: For notation software like MuseScore, Finale, or Sibelius
   - **PNG preview**: Visual sheet music (if MuseScore is installed)

### Real-time Transcription

Access the real-time transcription interface:
1. Navigate to `http://localhost:8001/realtime`
2. Click "Start" to begin live transcription
3. Play music into your microphone
4. See notes appear in real-time!

### MIDI Controller Input

To use a MIDI controller:
```python
from midi_controller import MIDIController, MIDIToAudioTranscription

# List available MIDI ports
controller = MIDIController()
controller.list_available_ports()

# Start live MIDI transcription
transcriber = MIDIToAudioTranscription()
transcriber.start_live_transcription()
```

### Command Line Examples

Test specific features:
```bash
# Test polyphonic transcription
python -c "from polyphonic_transcription import transcribe_polyphonic; print('Ready')"

# Test all future features
python test_future_features.py
```

## Project Structure

```
midi/
├── app.py                      # Flask web application with routing
├── audio_io.py                 # Audio loading and visualization
├── pitch_detect_improved.py    # Enhanced pitch detection algorithms
├── pitch_detect_advanced.py    # Advanced detection with tempo/rhythm
├── polyphonic_transcription.py # Multi-note simultaneous detection
├── key_chord_detection.py      # Key signature and chord analysis
├── instrument_recognition.py   # Timbre-based instrument classification
├── realtime_audio.py          # Real-time audio processing
├── midi_controller.py         # MIDI controller input handling
├── midi_writer_improved.py     # Improved MIDI generation
├── midi_writer_advanced.py     # Advanced MIDI with dynamics/tempo
├── notation.py                 # Basic MusicXML conversion
├── notation_advanced.py        # Advanced notation with measures/rests
├── templates/
│   ├── index.html             # Ghibli-inspired web interface
│   └── realtime.html          # Real-time transcription interface
├── static/                     # Upload directory and output files
├── requirements.txt            # Python dependencies
├── test_advanced_features.py   # Test suite for v2.0 features
└── test_future_features.py     # Test suite for v3.0 features
```

## Technical Details

### Advanced Algorithm Parameters

The enhanced transcription system uses:

**Pitch Detection:**
- **hop_length**: 512 samples (11.6ms at 44.1kHz)
- **Window function**: Hann window for cleaner frequency analysis
- **Magnitude threshold**: 0.1 (adaptive based on RMS energy)
- **Pitch smoothing**: 5-point median filter
- **Confidence weighting**: Weighted median for pitch selection

**Rhythm Analysis:**
- **Beat tracking**: Ellis dynamic programming algorithm
- **Onset detection**: Spectral flux with median aggregation
- **Quantization grid**: 16th note resolution (adjustable)
- **Tempo range**: 50-200 BPM automatic detection
- **Time signatures**: 3/4, 4/4, 6/8 (automatic detection)

**MIDI Generation:**
- **Velocity range**: 60-100 (dynamically adjusted)
- **Note overlap prevention**: Automatic trimming
- **Minimum note duration**: 50ms
- **Dynamic smoothing**: 5-note moving average

### Improvements Over Original

1. **✅ Fixed Note Overlap**: Notes are properly segmented with no overlaps
2. **✅ Dynamic Duration**: Note lengths based on actual performance
3. **✅ Rest Detection**: Silence properly identified and notated
4. **✅ Rhythm Accuracy**: Notes aligned to musical grid
5. **✅ Smooth Playback**: No more "glitchy" sounds or clicks
6. **🔄 Polyphony**: Still monophonic (future enhancement)

## Dependencies

Key libraries:
- `Flask`: Web framework
- `librosa`: Audio analysis and pitch detection
- `pretty_midi`: MIDI file creation
- `music21`: MusicXML generation
- `numpy`: Numerical computations
- `soundfile`: Audio file I/O

## Deployment

The application includes configuration for deployment:
- `runtime.txt`: Python version specification
- `gunicorn`: Production WSGI server

## License

This project is open source. Please check with the original repository for specific license details.

## Examples

### Transcription Results

The Advanced mode excels at:
- **Classical Music**: Proper tempo and measure organization
- **Pop/Rock**: Accurate rhythm with rest detection
- **Solo Instruments**: Clean note separation
- **Vocals**: Smooth pitch tracking with proper phrasing

### Console Output
```
[INFO] Detected tempo: 120.0 BPM
[INFO] Advanced MIDI written to static/output.mid
[INFO] Tempo: 120.0 BPM
[INFO] Time Signature: 4/4
[INFO] Total notes: 42
[INFO] Average note interval: 0.251s
[INFO] Most common interval: 0.250s
```

## Troubleshooting

### Common Issues

1. **No tempo detected**: Try the "Improved" mode for non-rhythmic audio
2. **Wrong time signature**: The system defaults to 4/4 for ambiguous cases
3. **Missing notes**: Lower the magnitude threshold in the code
4. **Too many notes**: Increase the minimum note duration

## New Features Documentation

### Polyphonic Transcription
- Uses harmonic product spectrum for fundamental frequency detection
- Supports up to 6 simultaneous notes by default
- Salience-based note detection with peak finding
- Handles complex chords and harmonies

### Key Signature Detection
- Implements Krumhansl-Schmuckler algorithm
- Correlates chroma vectors with major/minor profiles
- Provides confidence scores for detected keys
- Windowed analysis for consistency checking

### Chord Recognition
- Template matching against common chord types
- Supports major, minor, diminished, augmented, 7th chords
- Real-time chord progression tracking
- Exports chord progressions as MIDI

### Instrument Recognition
- Timbre feature extraction (MFCCs, spectral features)
- Heuristic classification based on acoustic properties
- Per-section instrument analysis
- Multi-instrument MIDI export

### Real-time Processing
- PyAudio-based audio streaming
- Configurable buffer sizes and processing intervals
- Monophonic and polyphonic modes
- Web-based real-time visualization

### MIDI Controller Support
- Compatible with all standard MIDI devices
- Real-time note and controller tracking
- Recording and playback capabilities
- Virtual MIDI port support

## Contributing

All major features have been implemented! Areas for further enhancement:
- Machine learning models for instrument recognition
- More sophisticated chord voicing detection
- Integration with DAWs
- Mobile app development
- Cloud-based processing

## Credits

- Original repository: [JustBottling/Music-transcription](https://github.com/JustBottling/Music-transcription)
- Enhanced fork: [Skarath13/midi](https://github.com/Skarath13/midi)
- UI Design: Inspired by Studio Ghibli's whimsical aesthetics
- Algorithms: Based on music information retrieval research