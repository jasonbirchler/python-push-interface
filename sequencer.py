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
            self.midi_output.send_stop()
            if self._thread:
                self._thread.join()
                
    def _play_loop(self):

        step_duration = 60.0 / (self.bpm * 4)  # 16th notes
        start_time = time.time()
        
        while not self._stop_event.is_set():
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Calculate current step based on elapsed time
            new_step = int((elapsed * self.bpm * 4 / 60)) % self.pattern.length
            
            # If we've moved to a new step, play notes
            if new_step != self.current_step:
                self.current_step = new_step
                notes_at_step = self.pattern.get_notes_at_step(self.current_step)

                for note in notes_at_step:
                    self.midi_output.send_note_on(self.midi_channel, note.note, note.velocity)
            
            time.sleep(0.01)  # 10ms sleep
