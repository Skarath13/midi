"""
MIDI Controller Input Module
Handles real-time MIDI input from controllers and keyboards
"""

import time
import threading
import queue
import mido
from collections import defaultdict
import numpy as np

class MIDIController:
    """
    Handle MIDI controller input for real-time music interaction.
    """
    
    def __init__(self, input_name=None, virtual=False):
        """
        Initialize MIDI controller handler.
        
        :param input_name: Name of MIDI input port (None for default)
        :param virtual: Create virtual MIDI port
        """
        self.input_name = input_name
        self.virtual = virtual
        
        # MIDI state
        self.active_notes = {}  # Track currently pressed notes
        self.control_values = defaultdict(int)  # CC values
        self.pitch_bend = 0
        self.current_program = 0
        
        # Event queues
        self.event_queue = queue.Queue()
        self.note_on_callbacks = []
        self.note_off_callbacks = []
        self.cc_callbacks = []
        
        # Threading
        self.is_running = False
        self.midi_thread = None
        self.inport = None
        
        # Recording
        self.is_recording = False
        self.recorded_events = []
        self.recording_start_time = None
        
    def list_available_ports(self):
        """
        List all available MIDI input ports.
        """
        print("[INFO] Available MIDI input ports:")
        for i, port in enumerate(mido.get_input_names()):
            print(f"  {i}: {port}")
        return mido.get_input_names()
    
    def connect(self):
        """
        Connect to MIDI input port.
        """
        available_ports = mido.get_input_names()
        
        if not available_ports and not self.virtual:
            print("[ERROR] No MIDI input ports available")
            return False
        
        try:
            if self.virtual:
                # Create virtual port
                self.inport = mido.open_input('Virtual MIDI Input', virtual=True)
                print("[INFO] Created virtual MIDI input port")
            elif self.input_name:
                # Open specific port
                self.inport = mido.open_input(self.input_name)
                print(f"[INFO] Connected to MIDI port: {self.input_name}")
            else:
                # Open first available port
                self.inport = mido.open_input(available_ports[0])
                print(f"[INFO] Connected to MIDI port: {available_ports[0]}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to connect to MIDI port: {e}")
            return False
    
    def midi_input_thread(self):
        """
        Thread for reading MIDI input.
        """
        while self.is_running:
            try:
                # Poll for MIDI messages
                for msg in self.inport.iter_pending():
                    self.process_midi_message(msg)
                
                time.sleep(0.001)  # Small delay to prevent CPU overload
                
            except Exception as e:
                print(f"[ERROR] MIDI input error: {e}")
    
    def process_midi_message(self, msg):
        """
        Process incoming MIDI message.
        """
        # Add to event queue
        self.event_queue.put(msg)
        
        # Record if enabled
        if self.is_recording:
            timestamp = time.time() - self.recording_start_time
            self.recorded_events.append((timestamp, msg))
        
        # Handle message types
        if msg.type == 'note_on' and msg.velocity > 0:
            self.handle_note_on(msg)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            self.handle_note_off(msg)
        elif msg.type == 'control_change':
            self.handle_control_change(msg)
        elif msg.type == 'pitchwheel':
            self.handle_pitch_bend(msg)
        elif msg.type == 'program_change':
            self.handle_program_change(msg)
    
    def handle_note_on(self, msg):
        """
        Handle note on message.
        """
        self.active_notes[msg.note] = {
            'velocity': msg.velocity,
            'channel': msg.channel,
            'time': time.time()
        }
        
        # Call callbacks
        for callback in self.note_on_callbacks:
            callback(msg.note, msg.velocity, msg.channel)
        
        # Print info
        note_name = self.midi_to_note_name(msg.note)
        print(f"Note ON: {note_name} (MIDI {msg.note}, velocity {msg.velocity})")
    
    def handle_note_off(self, msg):
        """
        Handle note off message.
        """
        if msg.note in self.active_notes:
            note_info = self.active_notes[msg.note]
            duration = time.time() - note_info['time']
            del self.active_notes[msg.note]
            
            # Call callbacks
            for callback in self.note_off_callbacks:
                callback(msg.note, duration, msg.channel)
            
            # Print info
            note_name = self.midi_to_note_name(msg.note)
            print(f"Note OFF: {note_name} (duration: {duration:.2f}s)")
    
    def handle_control_change(self, msg):
        """
        Handle control change message.
        """
        self.control_values[msg.control] = msg.value
        
        # Call callbacks
        for callback in self.cc_callbacks:
            callback(msg.control, msg.value, msg.channel)
        
        # Print common CC messages
        cc_names = {
            1: 'Modulation',
            7: 'Volume',
            10: 'Pan',
            11: 'Expression',
            64: 'Sustain Pedal',
            71: 'Resonance',
            74: 'Brightness'
        }
        
        cc_name = cc_names.get(msg.control, f'CC{msg.control}')
        print(f"Control Change: {cc_name} = {msg.value}")
    
    def handle_pitch_bend(self, msg):
        """
        Handle pitch bend message.
        """
        self.pitch_bend = msg.pitch
        print(f"Pitch Bend: {msg.pitch}")
    
    def handle_program_change(self, msg):
        """
        Handle program change message.
        """
        self.current_program = msg.program
        print(f"Program Change: {msg.program}")
    
    def start(self):
        """
        Start MIDI input handling.
        """
        if not self.inport:
            if not self.connect():
                return False
        
        self.is_running = True
        self.midi_thread = threading.Thread(target=self.midi_input_thread)
        self.midi_thread.start()
        
        print("[INFO] MIDI controller input started")
        return True
    
    def stop(self):
        """
        Stop MIDI input handling.
        """
        self.is_running = False
        
        if self.midi_thread:
            self.midi_thread.join()
        
        if self.inport:
            self.inport.close()
        
        print("[INFO] MIDI controller input stopped")
    
    def start_recording(self):
        """
        Start recording MIDI events.
        """
        self.is_recording = True
        self.recorded_events = []
        self.recording_start_time = time.time()
        print("[INFO] MIDI recording started")
    
    def stop_recording(self):
        """
        Stop recording and return recorded events.
        """
        self.is_recording = False
        print(f"[INFO] MIDI recording stopped. Recorded {len(self.recorded_events)} events")
        return self.recorded_events
    
    def save_recording(self, filename, tempo=120):
        """
        Save recorded MIDI events to file.
        """
        if not self.recorded_events:
            print("[WARNING] No events to save")
            return
        
        # Create MIDI file
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Add tempo
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))
        
        # Convert events to MIDI ticks
        ticks_per_beat = mid.ticks_per_beat
        last_time = 0
        
        for timestamp, msg in self.recorded_events:
            # Calculate delta time in ticks
            delta_time = timestamp - last_time
            delta_ticks = int(delta_time * tempo * ticks_per_beat / 60)
            
            # Create new message with time
            new_msg = msg.copy(time=delta_ticks)
            track.append(new_msg)
            
            last_time = timestamp
        
        # Save file
        mid.save(filename)
        print(f"[INFO] Recording saved to {filename}")
    
    def get_active_notes(self):
        """
        Get currently active notes.
        """
        return list(self.active_notes.keys())
    
    def get_control_value(self, cc_number):
        """
        Get current value of a control change.
        """
        return self.control_values.get(cc_number, 0)
    
    def register_note_on_callback(self, callback):
        """
        Register callback for note on events.
        """
        self.note_on_callbacks.append(callback)
    
    def register_note_off_callback(self, callback):
        """
        Register callback for note off events.
        """
        self.note_off_callbacks.append(callback)
    
    def register_cc_callback(self, callback):
        """
        Register callback for control change events.
        """
        self.cc_callbacks.append(callback)
    
    @staticmethod
    def midi_to_note_name(midi_note):
        """
        Convert MIDI note number to note name.
        """
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi_note // 12 - 1
        note = notes[midi_note % 12]
        return f"{note}{octave}"

class MIDIToAudioTranscription:
    """
    Bridge MIDI controller input to audio transcription features.
    """
    
    def __init__(self):
        self.controller = MIDIController()
        self.transcribed_notes = []
        self.is_transcribing = False
        
    def start_live_transcription(self):
        """
        Start live MIDI to notation transcription.
        """
        # Setup callbacks
        def on_note_on(note, velocity, channel):
            self.transcribed_notes.append({
                'type': 'note_on',
                'note': note,
                'velocity': velocity,
                'time': time.time()
            })
        
        def on_note_off(note, duration, channel):
            # Find corresponding note_on
            for i in range(len(self.transcribed_notes) - 1, -1, -1):
                if (self.transcribed_notes[i]['type'] == 'note_on' and 
                    self.transcribed_notes[i]['note'] == note):
                    self.transcribed_notes[i]['duration'] = duration
                    break
        
        self.controller.register_note_on_callback(on_note_on)
        self.controller.register_note_off_callback(on_note_off)
        
        # Start controller
        if self.controller.start():
            self.is_transcribing = True
            print("[INFO] Live MIDI transcription started")
            print("Play your MIDI controller. Press Ctrl+C to stop.")
            
            try:
                while True:
                    time.sleep(0.1)
                    
                    # Print chord if multiple notes active
                    active_notes = self.controller.get_active_notes()
                    if len(active_notes) >= 3:
                        chord_notes = [self.controller.midi_to_note_name(n) 
                                     for n in sorted(active_notes)]
                        print(f"Current chord: {', '.join(chord_notes)}")
                        
            except KeyboardInterrupt:
                print("\n[INFO] Stopping transcription...")
        
        self.controller.stop()
        self.is_transcribing = False
        
        return self.transcribed_notes
    
    def save_transcription(self, filename):
        """
        Save transcribed notes to MIDI file.
        """
        import pretty_midi
        
        pm = pretty_midi.PrettyMIDI()
        instrument = pretty_midi.Instrument(program=0)
        
        for note_event in self.transcribed_notes:
            if note_event['type'] == 'note_on' and 'duration' in note_event:
                note = pretty_midi.Note(
                    velocity=note_event['velocity'],
                    pitch=note_event['note'],
                    start=note_event['time'] - self.transcribed_notes[0]['time'],
                    end=note_event['time'] - self.transcribed_notes[0]['time'] + note_event['duration']
                )
                instrument.notes.append(note)
        
        pm.instruments.append(instrument)
        pm.write(filename)
        print(f"[INFO] Transcription saved to {filename}")

def demo_midi_controller():
    """
    Demo MIDI controller functionality.
    """
    controller = MIDIController()
    
    # List available ports
    ports = controller.list_available_ports()
    
    if not ports:
        print("[WARNING] No MIDI ports found. Creating virtual port...")
        controller = MIDIController(virtual=True)
    
    # Setup some fun callbacks
    def chord_detector(note, velocity, channel):
        active = controller.get_active_notes()
        if len(active) >= 3:
            print(f"🎹 Chord detected with {len(active)} notes!")
    
    def velocity_meter(note, velocity, channel):
        bars = '█' * (velocity // 10)
        print(f"Velocity: {bars} ({velocity})")
    
    controller.register_note_on_callback(chord_detector)
    controller.register_note_on_callback(velocity_meter)
    
    # Start and run
    if controller.start():
        print("\n" + "="*50)
        print("MIDI Controller Demo")
        print("Play your MIDI device!")
        print("="*50 + "\n")
        
        controller.start_recording()
        
        try:
            time.sleep(30)  # Run for 30 seconds
        except KeyboardInterrupt:
            pass
        
        events = controller.stop_recording()
        controller.stop()
        
        if events:
            controller.save_recording("midi_demo_recording.mid")

if __name__ == "__main__":
    # Run demo
    demo_midi_controller()