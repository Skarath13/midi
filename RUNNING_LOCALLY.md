# Running the Music Transcriber Locally

## Quick Start (Easiest Method)

```bash
python quick_start.py
```

This will:
- Check and install dependencies
- Start the server on port 8001
- Automatically open your browser

## Manual Setup

### 1. Install Dependencies

First, make sure you have Python 3.7+ installed, then:

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python app.py
```

The server will start on **http://localhost:8001**

### 3. Access the Application

Open your browser and go to: **http://localhost:8001**

## Alternative Methods

### Using the Shell Script (Mac/Linux)

```bash
./run_server.sh
```

### Test Before Running

To verify everything is set up correctly:

```bash
python test_server.py
```

## Troubleshooting

### Port Already in Use

If port 8001 is already in use, you can change it in `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=8002)  # Change to any available port
```

### Missing Dependencies

If you see import errors, make sure to install all dependencies:

```bash
pip install flask librosa pretty_midi music21 numpy soundfile
```

### MuseScore (Optional)

For PNG sheet music generation, install MuseScore and set the path:

```bash
# Mac
export MUSESCORE_PATH=/Applications/MuseScore.app/Contents/MacOS/mscore

# Windows
set MUSESCORE_PATH="C:\Program Files\MuseScore 3\bin\musescore.exe"

# Linux
export MUSESCORE_PATH=/usr/bin/musescore
```

## Features Available

Once running, you can:
1. Upload audio files (WAV, MP3, FLAC)
2. Choose transcription method
3. Download MIDI and MusicXML files
4. View transcription statistics

## Stopping the Server

Press `Ctrl+C` in the terminal to stop the server.

---

🎵 Enjoy transcribing your music! 🎼