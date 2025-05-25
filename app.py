import os
import traceback
from flask import Flask, request, render_template, send_from_directory, redirect, flash
import librosa
from audio_io import load_audio
from pitch_detect_improved import detect_midi_notes_improved, detect_midi_notes_with_onset
from pitch_detect_advanced import detect_midi_notes_advanced, detect_time_signature
from midi_writer_improved import write_midi_improved, write_midi_with_filtering
from midi_writer_advanced import write_midi_advanced, smooth_midi_dynamics
from notation import midi_to_sheet
from notation_advanced import midi_to_sheet_advanced, analyze_musical_structure
from music21 import environment

# Configure MuseScore path if available
mscore = os.getenv('MUSESCORE_PATH')
if mscore:
    us = environment.UserSettings()
    us['musescoreDirectPNGPath'] = mscore

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.config['ALLOWED_EXTENSIONS'] = {'wav', 'mp3', 'flac'}
app.secret_key = os.getenv('SECRET_KEY', 'replace-with-secure-secret')

# Ensure static folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            file = request.files.get('audio')
            if not file or not allowed_file(file.filename):
                flash('Please upload a valid WAV, MP3, or FLAC file.')
                return redirect(request.url)
            
            # Get transcription method from form
            method = request.form.get('method', 'improved')

            # Setup file paths
            ext = file.filename.rsplit('.', 1)[1].lower()
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f'input.{ext}')
            midi_path  = os.path.join(app.config['UPLOAD_FOLDER'], 'output.mid')
            xml_path   = os.path.join(app.config['UPLOAD_FOLDER'], 'output.musicxml')
            png_path   = os.path.join(app.config['UPLOAD_FOLDER'], 'output_sheet.png')

            # Save uploaded file
            file.save(audio_path)
            
            # Load and process audio
            y, sr = load_audio(audio_path)
            
            # Use selected transcription method
            tempo = None
            time_signature = None
            
            if method == 'onset':
                notes = detect_midi_notes_with_onset(y, sr)
                write_midi_improved(notes, midi_path)
            elif method == 'filtered':
                notes = detect_midi_notes_improved(y, sr)
                write_midi_with_filtering(notes, midi_path, min_duration=0.1, max_duration=1.5)
            elif method == 'advanced':
                # Use new advanced method with rhythm quantization
                notes, tempo = detect_midi_notes_advanced(y, sr, quantize=True, tempo_analysis=True)
                
                # Detect time signature with enhanced downbeat detection
                if tempo:
                    # Get onset envelope and beats for better time signature detection
                    onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
                    _, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
                    beat_times = librosa.frames_to_time(beats, sr=sr)
                    time_signature = detect_time_signature(beat_times, notes, onset_env, beats)
                else:
                    time_signature = (4, 4)
                
                # Write MIDI with advanced features
                write_midi_advanced(notes, midi_path, tempo=tempo, time_signature=time_signature)
            elif method == 'smooth':
                # Use advanced detection with smooth playback
                notes, tempo = detect_midi_notes_advanced(y, sr, quantize=False, tempo_analysis=True)
                smooth_midi_dynamics(notes, midi_path, tempo=tempo)
            else:  # default 'improved'
                notes = detect_midi_notes_improved(y, sr)
                write_midi_improved(notes, midi_path)
            
            # Generate MusicXML and PNG if MuseScore is available
            png_generated = False
            try:
                # Use advanced notation for advanced methods
                if method in ['advanced', 'smooth']:
                    if mscore:
                        # Try to generate with PNG using advanced method
                        midi_to_sheet_advanced(midi_path, xml_path, png_output=png_path, 
                                             musescore_path=mscore, tempo_bpm=tempo,
                                             time_signature=time_signature, add_rests=True,
                                             simplify_rhythms=(method == 'advanced'))
                        if os.path.exists(png_path):
                            png_generated = True
                    else:
                        # Just generate MusicXML without PNG
                        midi_to_sheet_advanced(midi_path, xml_path, png_output=None,
                                             tempo_bpm=tempo, time_signature=time_signature,
                                             add_rests=True, simplify_rhythms=(method == 'advanced'))
                else:
                    # Use original notation for other methods
                    if mscore:
                        # Try to generate with PNG
                        midi_to_sheet(midi_path, xml_path, png_output=png_path, musescore_path=mscore)
                        if os.path.exists(png_path):
                            png_generated = True
                    else:
                        # Just generate MusicXML without PNG
                        midi_to_sheet(midi_path, xml_path, png_output=None)
            except Exception as e:
                print(f"[WARNING] Sheet generation issue: {e}")
                # Ensure at least MusicXML is generated
                try:
                    midi_to_sheet(midi_path, xml_path, png_output=None)
                except:
                    pass

            return render_template(
                'index.html',
                audio_file=os.path.basename(audio_path),
                midi_file=os.path.basename(midi_path),
                xml_file=os.path.basename(xml_path),
                png_file=os.path.basename(png_path) if png_generated else None,
                num_notes=len(notes),
                method=method
            )

        # GET request
        return render_template('index.html')

    except Exception as e:
        tb = traceback.format_exc()
        app.logger.error('Unhandled exception in index():\n%s', tb)
        flash('Something went wrong. Please try again.')
        return render_template('index.html'), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)