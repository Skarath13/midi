"""
Real-time Audio Processing Module
Supports live audio input and streaming transcription
"""

import numpy as np
import pyaudio
import threading
import queue
import time
from collections import deque
import librosa

# Import our existing modules
from pitch_detect_advanced import detect_midi_notes_advanced
from polyphonic_transcription import extract_multi_pitch_salience, detect_polyphonic_notes
from key_chord_detection import detect_chord, extract_chroma_features

class RealtimeTranscriber:
    """
    Real-time audio transcriber with streaming capabilities.
    """
    
    def __init__(self, sample_rate=44100, channels=1, chunk_size=2048, 
                 buffer_duration=2.0, transcription_mode='monophonic'):
        """
        Initialize real-time transcriber.
        
        :param sample_rate: Audio sample rate
        :param channels: Number of audio channels
        :param chunk_size: Size of audio chunks to process
        :param buffer_duration: Duration of rolling buffer in seconds
        :param transcription_mode: 'monophonic' or 'polyphonic'
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.buffer_duration = buffer_duration
        self.transcription_mode = transcription_mode
        
        # Audio buffer (circular buffer for efficiency)
        buffer_size = int(sample_rate * buffer_duration)
        self.audio_buffer = deque(maxlen=buffer_size)
        
        # PyAudio setup
        self.p = pyaudio.PyAudio()
        self.stream = None
        
        # Threading
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.is_running = False
        self.audio_thread = None
        self.processing_thread = None
        
        # Results storage
        self.detected_notes = []
        self.current_chord = None
        self.current_pitch = None
        
        # Processing parameters
        self.hop_length = 512
        self.process_interval = 0.1  # Process every 100ms
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback for audio stream.
        """
        if status:
            print(f"[WARNING] Audio stream status: {status}")
        
        # Convert byte data to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Add to queue for processing
        self.audio_queue.put(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
    def audio_reader_thread(self):
        """
        Thread for reading audio from queue and updating buffer.
        """
        while self.is_running:
            try:
                # Get audio chunk from queue
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Add to circular buffer
                self.audio_buffer.extend(audio_chunk)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] Audio reader error: {e}")
    
    def processing_thread_func(self):
        """
        Thread for processing audio buffer and detecting notes.
        """
        last_process_time = time.time()
        
        while self.is_running:
            current_time = time.time()
            
            # Process at specified interval
            if current_time - last_process_time >= self.process_interval:
                try:
                    # Get current buffer as numpy array
                    if len(self.audio_buffer) > self.chunk_size:
                        buffer_array = np.array(list(self.audio_buffer))
                        
                        # Process based on mode
                        if self.transcription_mode == 'monophonic':
                            self.process_monophonic(buffer_array)
                        else:
                            self.process_polyphonic(buffer_array)
                        
                        # Detect current chord
                        self.process_chord(buffer_array)
                    
                    last_process_time = current_time
                    
                except Exception as e:
                    print(f"[ERROR] Processing error: {e}")
            
            # Small sleep to prevent CPU overload
            time.sleep(0.01)
    
    def process_monophonic(self, audio_buffer):
        """
        Process audio buffer for monophonic pitch detection.
        """
        # Use simple pitch detection for real-time
        pitches, magnitudes = librosa.piptrack(
            y=audio_buffer, 
            sr=self.sample_rate, 
            hop_length=self.hop_length
        )
        
        # Get most recent pitch
        if pitches.shape[1] > 0:
            # Last frame
            mag_column = magnitudes[:, -1]
            
            if mag_column.max() > 0.1:  # Threshold
                best_bin = mag_column.argmax()
                freq = pitches[best_bin, -1]
                
                if freq > 0:
                    midi_note = int(np.round(librosa.hz_to_midi(freq)))
                    self.current_pitch = midi_note
                    
                    # Add to results
                    result = {
                        'time': time.time(),
                        'pitch': midi_note,
                        'frequency': freq,
                        'confidence': mag_column.max()
                    }
                    self.result_queue.put(('pitch', result))
                else:
                    self.current_pitch = None
            else:
                self.current_pitch = None
    
    def process_polyphonic(self, audio_buffer):
        """
        Process audio buffer for polyphonic pitch detection.
        """
        # Extract multi-pitch salience (simplified for real-time)
        salience, midi_pitches = extract_multi_pitch_salience(
            audio_buffer, 
            self.sample_rate,
            hop_length=self.hop_length,
            n_fft=1024  # Smaller FFT for speed
        )
        
        # Get most recent frame
        if salience.shape[1] > 0:
            current_salience = salience[:, -1]
            
            # Find peaks
            threshold = 0.3
            active_pitches = []
            
            for i, sal in enumerate(current_salience):
                if sal > threshold * np.max(current_salience):
                    active_pitches.append((midi_pitches[i], sal))
            
            # Sort by salience and take top N
            active_pitches.sort(key=lambda x: x[1], reverse=True)
            active_pitches = active_pitches[:6]  # Max 6 notes
            
            if active_pitches:
                result = {
                    'time': time.time(),
                    'pitches': [p[0] for p in active_pitches],
                    'confidences': [p[1] for p in active_pitches]
                }
                self.result_queue.put(('polyphonic', result))
    
    def process_chord(self, audio_buffer):
        """
        Process audio buffer for chord detection.
        """
        # Extract chroma features
        chroma = librosa.feature.chroma_cqt(
            y=audio_buffer,
            sr=self.sample_rate,
            hop_length=self.hop_length
        )
        
        if chroma.shape[1] > 0:
            # Average over recent frames
            recent_frames = min(10, chroma.shape[1])
            mean_chroma = np.mean(chroma[:, -recent_frames:], axis=1)
            
            # Detect chord
            from key_chord_detection import detect_chord
            root, chord_type, confidence = detect_chord(mean_chroma, threshold=0.5)
            
            if root is not None:
                chord_name = f"{root}{'' if chord_type == 'major' else chord_type}"
                
                if chord_name != self.current_chord:
                    self.current_chord = chord_name
                    result = {
                        'time': time.time(),
                        'chord': chord_name,
                        'confidence': confidence
                    }
                    self.result_queue.put(('chord', result))
    
    def start(self):
        """
        Start real-time transcription.
        """
        print(f"[INFO] Starting real-time transcription ({self.transcription_mode} mode)...")
        
        self.is_running = True
        
        # Start audio stream
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self.audio_callback
        )
        
        # Start threads
        self.audio_thread = threading.Thread(target=self.audio_reader_thread)
        self.processing_thread = threading.Thread(target=self.processing_thread_func)
        
        self.audio_thread.start()
        self.processing_thread.start()
        
        self.stream.start_stream()
        
        print("[INFO] Real-time transcription started. Press Ctrl+C to stop.")
    
    def stop(self):
        """
        Stop real-time transcription.
        """
        print("[INFO] Stopping real-time transcription...")
        
        self.is_running = False
        
        # Stop stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Wait for threads
        if self.audio_thread:
            self.audio_thread.join()
        if self.processing_thread:
            self.processing_thread.join()
        
        # Cleanup
        self.p.terminate()
        
        print("[INFO] Real-time transcription stopped.")
    
    def get_results(self, timeout=0.1):
        """
        Get transcription results from queue.
        
        :param timeout: Queue timeout
        :return: Tuple of (result_type, result_data) or None
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

def demo_realtime_transcription(duration=10, mode='monophonic'):
    """
    Demo real-time transcription.
    
    :param duration: Duration in seconds
    :param mode: 'monophonic' or 'polyphonic'
    """
    transcriber = RealtimeTranscriber(transcription_mode=mode)
    
    try:
        transcriber.start()
        
        start_time = time.time()
        note_history = []
        
        print("\n" + "="*50)
        print(f"Real-time {mode} transcription active")
        print("Play some music into your microphone!")
        print("="*50 + "\n")
        
        while time.time() - start_time < duration:
            result = transcriber.get_results()
            
            if result:
                result_type, data = result
                
                if result_type == 'pitch':
                    note_name = librosa.midi_to_note(data['pitch'])
                    print(f"Note: {note_name} (MIDI {data['pitch']}, "
                          f"{data['frequency']:.1f} Hz, "
                          f"confidence: {data['confidence']:.2f})")
                    note_history.append(data)
                
                elif result_type == 'polyphonic':
                    notes = [librosa.midi_to_note(p) for p in data['pitches']]
                    print(f"Chord: {', '.join(notes)}")
                
                elif result_type == 'chord':
                    print(f"Detected chord: {data['chord']} "
                          f"(confidence: {data['confidence']:.2f})")
            
            time.sleep(0.05)
        
        print(f"\n[INFO] Recorded {len(note_history)} note events")
        
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    
    finally:
        transcriber.stop()

class RealtimeVisualizer:
    """
    Simple console-based visualizer for real-time transcription.
    """
    
    @staticmethod
    def create_note_display(midi_note, width=50):
        """
        Create a visual representation of a note.
        """
        # Note position on a simplified keyboard
        octave = midi_note // 12
        note_in_octave = midi_note % 12
        
        # Create keyboard visualization
        keyboard = [' '] * width
        position = int((midi_note - 21) / 88 * width)  # 88 keys, starting from A0
        
        if 0 <= position < width:
            keyboard[position] = '█'
        
        return ''.join(keyboard)
    
    @staticmethod
    def visualize_realtime(duration=30):
        """
        Run real-time visualization.
        """
        transcriber = RealtimeTranscriber(transcription_mode='monophonic')
        
        try:
            transcriber.start()
            
            print("\033[2J\033[H")  # Clear screen
            print("REAL-TIME MUSIC TRANSCRIPTION")
            print("="*60)
            print("Play music into your microphone")
            print("="*60)
            
            start_time = time.time()
            last_notes = deque(maxlen=10)  # Keep last 10 notes
            
            while time.time() - start_time < duration:
                result = transcriber.get_results(timeout=0.05)
                
                if result and result[0] == 'pitch':
                    data = result[1]
                    note_name = librosa.midi_to_note(data['pitch'])
                    last_notes.append((note_name, data['pitch'], time.time()))
                
                # Update display
                print("\033[8;0H")  # Move cursor to line 8
                print("\nCurrent Notes:")
                print("-"*60)
                
                # Show recent notes
                current_time = time.time()
                for note_name, midi_note, note_time in last_notes:
                    age = current_time - note_time
                    if age < 2.0:  # Show notes from last 2 seconds
                        opacity = int((2.0 - age) / 2.0 * 10)
                        bar = RealtimeVisualizer.create_note_display(midi_note)
                        print(f"{note_name:>4} |{bar}| {'*' * opacity}")
                
                print("\n" + " "*60)  # Clear remaining lines
                
        except KeyboardInterrupt:
            print("\n[INFO] Visualization stopped")
        
        finally:
            transcriber.stop()

if __name__ == "__main__":
    # Run demo
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'visualize':
        RealtimeVisualizer.visualize_realtime(duration=60)
    else:
        # Run basic demo
        print("Starting monophonic transcription demo...")
        demo_realtime_transcription(duration=10, mode='monophonic')
        
        print("\nStarting polyphonic transcription demo...")
        demo_realtime_transcription(duration=10, mode='polyphonic')