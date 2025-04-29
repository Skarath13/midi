# notation.py
from music21 import converter, environment

def midi_to_sheet(midi_path, xml_output, png_output=None, musescore_path=None):
    """
    Convert a MIDI file into MusicXML (and optionally render PNG).
    :param midi_path: path to input .mid
    :param xml_output: path to write .musicxml
    :param png_output: if provided, path to write rendered PNG
    :param musescore_path: if provided, sets MuseScore executable path
    """
    # parse into a music21 score
    score = converter.parse(midi_path)

    # configure MuseScore if given
    if musescore_path:
        us = environment.UserSettings()
        us['musescoreDirectPNGPath'] = musescore_path

    # write MusicXML
    score.write('musicxml', fp=xml_output)
    print(f"[INFO] MusicXML written to {xml_output}")

    # render to PNG in-colab/IDE if requested
    if png_output:
        img = score.write('musicxml.png')
        # move or rename the auto-generated PNG
        import os, shutil
        shutil.move(img, png_output)
        print(f"[INFO] PNG score written to {png_output}")