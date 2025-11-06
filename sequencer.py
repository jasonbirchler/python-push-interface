import time
import threading
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Note:
    step: int
    note: int
    velocity: int

class Pattern:
    def __init__(self, length: int = 16):
        self.length = max(1, min(64, length))  # Clamp to 1-64
        self.notes: List[Note] = []
        self.current_step = 0

    def add_note(self, step: int, note: int, velocity: int = 100):
        # Only add note if step is within pattern length
        if 0 <= step < self.length:
            # Remove existing note at this step if any
            self.notes = [n for n in self.notes if n.step != step]
            # Add new note
            self.notes.append(Note(step, note, velocity))

    def remove_note(self, step: int):
        self.notes = [n for n in self.notes if n.step != step]

    def get_notes_at_step(self, step: int) -> List[Note]:
        return [n for n in self.notes if n.step == step]

    def clear_step(self, step: int):
        self.notes = [n for n in self.notes if n.step != step]

class Sequencer:
    def __init__(self, midi_output, bpm: int = 120):
        self.midi_output = midi_output
        self.bpm = bpm
        self.tracks = [Pattern() for _ in range(8)]  # 8 tracks
        self.track_channels = [1] * 8  # MIDI channel per track
        self.is_playing = False
        self.current_steps = [0] * 8  # Individual step counter per track
        self.current_track = 0  # Active track for editing
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._active_notes = set()  # Track active notes
        
        # MIDI clock sync
        self.external_sync = False
        self._clock_count = 0
        self._last_clock_time = None
        self._clock_times = []

    @property
    def current_step(self) -> int:
        """Backward compatibility property - return current step of first track"""
        return self.current_steps[0] if self.current_steps else 0
    
    @current_step.setter
    def current_step(self, value: int):
        """Backward compatibility setter - set first track's step"""
        if self.current_steps:
            self.current_steps[0] = value

    def set_bpm(self, bpm: int):
        self.bpm = bpm

    def set_midi_channel(self, channel: int):
        self.track_channels[self.current_track] = max(1, min(16, channel))

    def set_track_channel(self, track: int, channel: int):
        if 0 <= track < 8:
            self.track_channels[track] = max(1, min(16, channel))

    def set_track_port(self, track: int, port_name: str):
        if not hasattr(self, '_track_ports'):
            self._track_ports = {}
        self._track_ports[track] = port_name

    def set_track_device(self, track: int, device):
        if not hasattr(self, '_track_devices'):
            self._track_devices = {}
        self._track_devices[track] = device

    def set_pattern_length(self, track: int, length: int):
        """Set pattern length for specific track (1-64)"""
        if 0 <= track < 8:
            old_length = self.tracks[track].length
            self.tracks[track].length = max(1, min(64, length))
            
            # Clear notes beyond new length
            if old_length > self.tracks[track].length:
                self.tracks[track].notes = [
                    note for note in self.tracks[track].notes
                    if note.step < self.tracks[track].length
                ]
            
            print(f"Track {track} pattern length: {old_length} -> {self.tracks[track].length}")

    def get_pattern_length(self, track: int) -> int:
        """Get pattern length for specific track"""
        if 0 <= track < 8:
            return self.tracks[track].length
        return 16  # Default

    def get_current_step(self, track: int) -> int:
        """Get current step for specific track"""
        if 0 <= track < 8:
            return self.current_steps[track]
        return 0

    def _send_transport_to_active_devices(self, message_type):
        """Send start/stop only to devices with send_transport=true"""
        if not hasattr(self, '_track_devices'):
            return

        for track_idx, device in self._track_devices.items():
            if hasattr(device, 'send_transport') and device.send_transport:
                if message_type == 'start':
                    self.midi_output.send_start()
                elif message_type == 'stop':
                    self.midi_output.send_stop()
                    
    def handle_midi_clock(self):
        """Handle incoming MIDI clock pulse"""
        current_time = time.time()
        self._clock_count += 1
        
        # Debug: Print every 96th clock (whole note) to reduce noise
        if self._clock_count % 96 == 0:
            print(f"External sync: BPM {self.bpm}")
        
        # Forward clock to all devices
        self.midi_output.send_clock()
        
        # Calculate BPM from clock timing (24 clocks per quarter note)
        if self._last_clock_time:
            self._clock_times.append(current_time - self._last_clock_time)
            if len(self._clock_times) > 24:
                self._clock_times.pop(0)
                
            if len(self._clock_times) >= 24:
                avg_interval = sum(self._clock_times) / len(self._clock_times)
                quarter_note_time = avg_interval * 24
                new_bpm = round(60.0 / quarter_note_time, 1)
                if abs(new_bpm - self.bpm) > 0.1:  # Only update if significant change
                    self.bpm = new_bpm
                    print(f"BPM updated to: {self.bpm}")
                
        self._last_clock_time = current_time
        
        # Trigger step on every 6th clock (16th notes)
        if self.external_sync and self.is_playing and self._clock_count % 6 == 0:
            self._trigger_step()
            
    def handle_midi_start(self):
        """Handle incoming MIDI start"""
        print("MIDI Start received - switching to external sync")
        self._clock_count = 0
        self.current_steps = [0] * 8  # Reset all track step counters
        self.external_sync = True
        self.play()
        
    def handle_midi_stop(self):
        """Handle incoming MIDI stop"""
        print("MIDI Stop received - switching to internal sync")
        self.external_sync = False
        self.stop()

    def set_current_track(self, track: int):
        if 0 <= track < 8:
            self.current_track = track

    def play(self):
        if not self.is_playing:
            self.is_playing = True
            self._stop_event.clear()
            # Send start only to devices that want transport messages
            self._send_transport_to_active_devices('start')
            self._thread = threading.Thread(target=self._play_loop)
            self._thread.start()


    def stop(self):
        if self.is_playing:
            self.is_playing = False
            self._stop_event.set()

            # Send note-off for all active notes
            for channel, note, port_name in self._active_notes:
                self.midi_output.send_note_off(channel, note, port_name)
            self._active_notes.clear()

            # Send stop only to devices that want transport messages
            self._send_transport_to_active_devices('stop')
            if self._thread:
                self._thread.join()

    def _play_loop(self):
        step_duration = 60.0 / (self.bpm * 4)  # 16th notes
        next_step_time = time.time()
        self.note_off_time = None
        self.current_step_notes = set()

        while not self._stop_event.is_set():
            current_time = time.time()

            # Send note-off for previous step's notes
            if self.note_off_time and current_time >= self.note_off_time:
                for channel, note, port_name in self.current_step_notes:
                    self.midi_output.send_note_off(channel, note, port_name)
                    self._active_notes.discard((channel, note, port_name))
                self.current_step_notes.clear()
                self.note_off_time = None

            # Check if it's time for the next step (only for internal timing)
            if not self.external_sync and current_time >= next_step_time:
                self._trigger_step()
                next_step_time += step_duration

            time.sleep(0.01)  # Small sleep to prevent CPU spinning
            
    def _trigger_step(self):
        """Trigger notes for current step - advance each track independently"""
        # Send note-off for previous step's notes first
        for channel, note, port_name in self.current_step_notes:
            self.midi_output.send_note_off(channel, note, port_name)
            self._active_notes.discard((channel, note, port_name))
        self.current_step_notes.clear()
        
        # Play notes for all tracks at their current steps
        total_notes = 0
        for track_idx, track_pattern in enumerate(self.tracks):
            # Check if track should be audible
            if hasattr(self, 'app_ref') and self.app_ref and not self.app_ref._is_track_audible(track_idx):
                continue
                
            # Use this track's current step position
            current_track_step = self.current_steps[track_idx]
            notes_at_step = track_pattern.get_notes_at_step(current_track_step)
            total_notes += len(notes_at_step)

            for note in notes_at_step:
                channel = self.track_channels[track_idx]
                port_name = getattr(self, '_track_ports', {}).get(track_idx)
                print(f"Track {track_idx} Step {current_track_step}: Playing note {note.note} on channel {channel} port {port_name}")
                self.midi_output.send_note_on(channel, note.note, note.velocity, port_name)
                self._active_notes.add((channel, note.note, port_name))
                self.current_step_notes.add((channel, note.note, port_name))

        # Schedule note-off for end of this step
        step_duration = 60.0 / (self.bpm * 4)
        self.note_off_time = time.time() + step_duration * 0.9

        print(f"Polyrhythmic trigger: {total_notes} total notes across all tracks")
        
        # Store previous steps before advancing
        previous_steps = self.current_steps.copy()
        
        # Advance each track independently based on its pattern length
        for track_idx, track_pattern in enumerate(self.tracks):
            self.current_steps[track_idx] = (self.current_steps[track_idx] + 1) % track_pattern.length
        
        # Call pad update callback if available
        if hasattr(self, '_update_pad_colors_callback') and self._update_pad_colors_callback:
            self._update_pad_colors_callback()
        
        # Only publish step change event if any track step actually changed
        if hasattr(self, '_publish_step_event') and self._publish_step_event:
            for track_idx in range(8):
                if previous_steps[track_idx] != self.current_steps[track_idx]:
                    self._publish_step_event()
                    break
