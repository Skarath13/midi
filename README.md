# Music Transcription Tool

A web-based application that automatically transcribes audio files into MIDI and sheet music notation. Upload a WAV, MP3, or FLAC file and receive downloadable MIDI and MusicXML files.

## Features

- **Audio Format Support**: Accepts WAV, MP3, and FLAC audio files
- **Pitch Detection**: Uses librosa's pitch tracking algorithm to detect musical notes
- **MIDI Generation**: Converts detected notes into standard MIDI format
- **Sheet Music**: Generates MusicXML files for notation software
- **Web Interface**: Simple Flask-based interface for easy file upload and download
- **Waveform Visualization**: Displays audio waveform of uploaded files

## How It Works

1. **Audio Analysis**: The application uses `librosa.piptrack()` to analyze the frequency content of the audio
2. **Note Detection**: Identifies the dominant pitch at each time frame and converts frequencies to MIDI note numbers
3. **MIDI Creation**: Uses `pretty_midi` to construct a MIDI file with detected notes
4. **Notation Export**: Converts MIDI to MusicXML format using `music21` library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JustBottling/Music-transcription.git
cd Music-transcription
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

2. Open your browser to `http://localhost:5000`

3. Upload an audio file and click "Transcribe Now"

4. Download the generated MIDI and MusicXML files

### Command Line

For direct processing without the web interface:
```bash
python main.py
```
This expects an `input.wav` file in the project directory and generates:
- `transcription_output.mid`
- `output_sheet.musicxml`
- `output_sheet.png` (if MuseScore is configured)

## Project Structure

```
Music-transcription/
├── app.py              # Flask web application
├── audio_io.py         # Audio loading and visualization
├── pitch_detect.py     # Pitch detection algorithm
├── midi_writer.py      # MIDI file generation
├── notation.py         # MusicXML conversion
├── main.py             # Command-line interface
├── templates/
│   └── index.html      # Web interface template
└── static/             # Upload directory for web app
```

## Technical Details

### Pitch Detection Parameters

The pitch detection algorithm uses:
- **hop_length**: 512 samples (time resolution between frames)
- **mag_threshold**: 0.1 (minimum magnitude to consider a frame)
- **default_duration**: 0.4 seconds per note

### Known Issues

1. **Note Overlap**: The current implementation assigns a fixed duration (0.4s) to each detected note, which can cause overlapping notes and a "glitchy" sound in the MIDI playback.

2. **Polyphony**: The algorithm only detects the dominant pitch per frame, missing harmonies and chords.

3. **Note Segmentation**: No note onset/offset detection - every frame with sufficient magnitude generates a new note.

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

## Contributing

Contributions are welcome! Areas for improvement:
- Better note onset/offset detection
- Polyphonic transcription support
- Tempo and rhythm detection
- Real-time audio processing