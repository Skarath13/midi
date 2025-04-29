from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
import os
from audio_io       import load_audio, plot_waveform
from pitch_detect   import detect_midi_notes
from midi_writer    import write_midi
from notation       import midi_to_sheet

app = Flask(__name__)
app.config['UPLOAD_FOLDER']   = 'static'
app.config['ALLOWED_EXTENSIONS'] = {'wav', 'mp3', 'flac'}
app.secret_key = 'replace-with-a-secure-secret'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('audio')
        if not file or not allowed_file(file.filename):
            flash('Please upload an audio file (wav, mp3, flac).')
            return redirect(request.url)

        # 1) Save upload
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'input.' + file.filename.rsplit('.',1)[1])
        file.save(audio_path)

        # 2) Process
        y, sr = load_audio(audio_path)
        notes = detect_midi_notes(y, sr)
        midi_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.mid')
        write_midi(notes, midi_path)

        xml_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.musicxml')
        png_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_sheet.png')
        midi_to_sheet(midi_path, xml_path, png_output=png_path)

        return render_template('index.html',
                               audio_file=os.path.basename(audio_path),
                               midi_file=os.path.basename(midi_path),
                               xml_file=os.path.basename(xml_path),
                               png_file=os.path.basename(png_path))

    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)