import time
import threading
from typing import List, Optional
from sequencer import Sequencer, Pattern, Note
from .sequencer_state import SequencerState
from .sequencer_event_bus import SequencerEventBus, SequencerEvent, EventType

class SequencerEngine:
    """Core sequencer logic with no UI dependencies"""
    
    def __init__(self, midi_output):
        self.midi_output = midi_output
        self.event_bus = SequencerEventBus()
        
        # Use existing Sequencer internally but expose clean interface
        self._internal_sequencer = Sequencer(midi_output)
        # No callback - use pure event-driven approach
        
    # Removed callback - using main loop updates instead
    
    # Command methods (state-changing operations)
    def play(self) -> None:
        """Start playback"""
        was_playing = self.is_playing
        self._internal_sequencer.play()
        if not was_playing:
            self.event_bus.publish(SequencerEvent(
                type=EventType.PLAY_STATE_CHANGED,
                data={'is_playing': True}
            ))
    
    def stop(self) -> None:
        """Stop playback"""
        was_playing = self.is_playing
        self._internal_sequencer.stop()
        if was_playing:
            self.event_bus.publish(SequencerEvent(
                type=EventType.PLAY_STATE_CHANGED,
                data={'is_playing': False}
            ))
    
    def set_bpm(self, bpm: int) -> None:
        """Set BPM"""
        old_bpm = self.bpm
        self._internal_sequencer.set_bpm(bpm)
        if old_bpm != bpm:
            self.event_bus.publish(SequencerEvent(
                type=EventType.BPM_CHANGED,
                data={'bpm': bpm, 'old_bpm': old_bpm}
            ))
    
    def add_note(self, track: int, step: int, note: int, velocity: int) -> None:
        """Add note to track at step"""
        if 0 <= track < len(self._internal_sequencer.tracks):
            self._internal_sequencer.tracks[track].add_note(step, note, velocity)
            self.event_bus.publish(SequencerEvent(
                type=EventType.PATTERN_MODIFIED,
                data={'track': track, 'step': step, 'note': note, 'velocity': velocity, 'action': 'add'}
            ))
    
    def remove_note(self, track: int, step: int) -> None:
        """Remove note from track at step"""
        if 0 <= track < len(self._internal_sequencer.tracks):
            self._internal_sequencer.tracks[track].clear_step(step)
            self.event_bus.publish(SequencerEvent(
                type=EventType.PATTERN_MODIFIED,
                data={'track': track, 'step': step, 'action': 'remove'}
            ))
    
    def set_track_channel(self, track: int, channel: int) -> None:
        """Set MIDI channel for track"""
        self._internal_sequencer.set_track_channel(track, channel)
    
    def set_track_port(self, track: int, port: str) -> None:
        """Set MIDI port for track"""
        self._internal_sequencer.set_track_port(track, port)
    
    def set_track_device(self, track: int, device) -> None:
        """Set device for track"""
        self._internal_sequencer.set_track_device(track, device)
    
    # Query methods (read-only)
    @property
    def is_playing(self) -> bool:
        """Check if sequencer is playing"""
        return self._internal_sequencer.is_playing
    
    @property
    def current_step(self) -> int:
        """Get current step"""
        return self._internal_sequencer.current_step
    
    @property
    def bpm(self) -> int:
        """Get current BPM"""
        return self._internal_sequencer.bpm
    
    @property
    def current_track(self) -> int:
        """Get current track (for compatibility)"""
        return 0  # Will be managed by UI adapter
    
    def get_state(self) -> SequencerState:
        """Get immutable state snapshot"""
        return SequencerState(
            is_playing=self.is_playing,
            current_step=self.current_step,
            bpm=self.bpm,
            tracks=tuple(self._internal_sequencer.tracks),
            current_track=self.current_track
        )
    
    def get_track_notes(self, track: int) -> List[Note]:
        """Get all notes for a track"""
        if 0 <= track < len(self._internal_sequencer.tracks):
            notes = []
            for step in range(16):
                notes.extend(self._internal_sequencer.tracks[track].get_notes_at_step(step))
            return notes
        return []
    
    def handle_midi_clock(self) -> None:
        """Handle MIDI clock (delegate to internal sequencer)"""
        self._internal_sequencer.handle_midi_clock()
    
    def handle_midi_start(self) -> None:
        """Handle MIDI start (delegate to internal sequencer)"""
        self._internal_sequencer.handle_midi_start()
    
    def handle_midi_stop(self) -> None:
        """Handle MIDI stop (delegate to internal sequencer)"""
        self._internal_sequencer.handle_midi_stop()