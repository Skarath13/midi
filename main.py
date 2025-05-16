# main.py
import os
from audio_io    import load_audio, plot_waveform
from pitch_detect import detect_midi_notes
from midi_writer  import write_midi
from notation     import midi_to_sheet

def main():
    # 1) Define file paths
    audio_file = "input.wav"
    midi_file  = "transcription_output.mid"
    xml_file   = "output_sheet.musicxml"
    png_file   = "output_sheet.png"
    # Optionally set this if you have MuseScore locally:
    musescore_exe = ""  # e.g., r"C:/Program Files/MuseScore 4/bin/MuseScore4.exe"
    # If you have MuseScore installed, you can set the path to the executable here.
    # This is optional, but it allows you to convert the MIDI file to sheet music automatically.
    # If you don't have MuseScore, you can manually convert the MIDI file to sheet music using the MuseScore application.
    musescore_exe = "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"
    # e.g., r"C:/Program Files/MuseScore 4/bin/MuseScore4.exe"

    # 2) Load & visualize
    y, sr = load_audio(audio_file)
    plot_waveform(y, sr)

    # 3) Detect notes
    notes = detect_midi_notes(y, sr)
    print(f"[INFO] Detected {len(notes)} notes")

    # 4) Write MIDI
    write_midi(notes, midi_file)

    # 5) Convert to sheet music
    midi_to_sheet(midi_file, xml_file, png_output=png_file,
                  musescore_path=musescore_exe)

if __name__ == "__main__":
    # Ensure input exists
    if not os.path.exists("input.wav"):
        print("[ERROR] Please put an 'input.wav' file in the project folder.")
    else:
        main()