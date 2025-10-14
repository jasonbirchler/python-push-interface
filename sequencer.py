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
        self.length = length
        self.notes: List[Note] = []
        self.current_step = 0
        
    def add_note(self, step: int, note: int, velocity: int = 100):
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
        self.pattern = Pattern()
        self.is_playing = False
        self.current_step = 0
        self.midi_channel = 1
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._active_notes = set()  # Track active notes
        
    def set_bpm(self, bpm: int):
        self.bpm = bpm
        
    def set_midi_channel(self, channel: int):
        self.midi_channel = max(1, min(16, channel))
        
    def play(self):
        if not self.is_playing:
    
            self.is_playing = True
            self._stop_event.clear()
            self.midi_output.send_start()
            self._thread = threading.Thread(target=self._play_loop)
            self._thread.start()

            
    def stop(self):
        if self.is_playing:
            self.is_playing = False
            self._stop_event.set()

            # Send note-off for all active notes
            for note in self._active_notes:
                self.midi_output.send_note_off(self.midi_channel, note)
            self._active_notes.clear()

            self.midi_output.send_stop()
            if self._thread:
                self._thread.join()
                
    def _play_loop(self):
        step_duration = 60.0 / (self.bpm * 4)  # 16th notes
        next_step_time = time.time()
        note_off_time = None
        current_step_notes = set()
        
        while not self._stop_event.is_set():
            current_time = time.time()
            
            # Send note-off for previous step's notes
            if note_off_time and current_time >= note_off_time:
                for note in current_step_notes:
                    self.midi_output.send_note_off(self.midi_channel, note)
                    self._active_notes.discard(note)
                current_step_notes.clear()
                note_off_time = None
            
            # Check if it's time for the next step
            if current_time >= next_step_time:
                # Play notes at current step
                notes_at_step = self.pattern.get_notes_at_step(self.current_step)
                print(f"Step {self.current_step}: {len(notes_at_step)} notes")

                for note in notes_at_step:
                    print(f"Playing note {note.note} on channel {self.midi_channel}")
                    self.midi_output.send_note_on(self.midi_channel, note.note, note.velocity)
                    self._active_notes.add(note.note)
                    current_step_notes.add(note.note)

                # Schedule note-off for end of this step
                if current_step_notes:
                    note_off_time = next_step_time + step_duration * 0.9  # 90% of step duration

                # Advance to next step
                self.current_step = (self.current_step + 1) % self.pattern.length
                next_step_time += step_duration

                # Update pad colors from sequencer thread
                if hasattr(self, '_update_pad_colors_callback') and self._update_pad_colors_callback:
                    self._update_pad_colors_callback()

            time.sleep(0.01)  # Small sleep to prevent CPU spinning
