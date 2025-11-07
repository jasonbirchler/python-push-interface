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
        # Inject event publishing into internal sequencer
        self._internal_sequencer._event_bus = self.event_bus
        self._internal_sequencer._publish_step_event = self._publish_step_event
        # Initialize preserved notes and range tracking storage
        self._internal_sequencer._preserved_notes = {}
        self._internal_sequencer._range_starts = {}
        
    def _publish_step_event(self):
        """Publish step change event"""
        self.event_bus.publish(SequencerEvent(
            type=EventType.STEP_CHANGED,
            data={'current_step': self.current_step}
        ))
    
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
    
    # Polyrhythmic functionality
    def set_pattern_length(self, track: int, length: int, range_start: int = 0) -> None:
        """Set pattern length for specific track (1-64) with optional range positioning"""
        old_length = self.get_pattern_length(track)
        old_range_start = getattr(self._internal_sequencer, '_range_starts', {})[track] if track in getattr(self._internal_sequencer, '_range_starts', {}) else 0
        self._internal_sequencer.set_pattern_length(track, length, range_start)
        
        if old_length != length or old_range_start != range_start:
            self.event_bus.publish(SequencerEvent(
                type=EventType.PATTERN_LENGTH_CHANGED,
                data={'track': track, 'length': length, 'range_start': range_start, 'old_length': old_length, 'old_range_start': old_range_start}
            ))

    def get_pattern_length(self, track: int) -> int:
        """Get pattern length for specific track"""
        return self._internal_sequencer.get_pattern_length(track)

    def get_current_step(self, track: int) -> int:
        """Get current step for specific track"""
        return self._internal_sequencer.get_current_step(track)

    @property
    def track_steps(self) -> List[int]:
        """Get current step for all tracks"""
        return self._internal_sequencer.current_steps.copy()
    
    # Query methods (read-only)
    @property
    def is_playing(self) -> bool:
        """Check if sequencer is playing"""
        return self._internal_sequencer.is_playing
    
    @property
    def current_step(self) -> int:
        """Get current step for compatibility (use track_steps for polyrhythmic)"""
        return self._internal_sequencer.current_steps[0]  # Return first track for compatibility
    
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
