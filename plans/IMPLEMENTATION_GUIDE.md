# Implementation Guide: Sequencer Decoupling

## Overview

This guide provides step-by-step instructions for implementing the decoupled architecture. It's designed to be executed incrementally, allowing you to test each phase before moving to the next.

## Phase 1: Core Abstraction (Foundation)

### Step 1.1: Create SequencerState (Immutable State Model)

**File**: `core/sequencer_state.py`

```python
from dataclasses import dataclass
from typing import Tuple, List, FrozenSet
from sequencer import Pattern, Note

@dataclass(frozen=True)
class SequencerState:
    """Immutable snapshot of sequencer state"""
    is_playing: bool
    current_step: int
    bpm: int
    tracks: Tuple[Pattern, ...]
    track_channels: Tuple[int, ...]
    current_track: int
    external_sync: bool
    
    def get_notes_at_step(self, track: int, step: int) -> List[Note]:
        """Query notes at a specific step"""
        if 0 <= track < len(self.tracks):
            return self.tracks[track].get_notes_at_step(step)
        return []
    
    def get_track_pattern(self, track: int) -> Pattern:
        """Get pattern for a track"""
        if 0 <= track < len(self.tracks):
            return self.tracks[track]
        return None
    
    def is_track_audible(self, track: int) -> bool:
        """Check if track should play (for mute/solo logic)"""
        # This will be extended by adapters
        return True
```

### Step 1.2: Create SequencerEventBus (Pub/Sub System)

**File**: `core/sequencer_event_bus.py`

```python
from dataclasses import dataclass
from typing import Callable, Dict, List
from enum import Enum

class EventType(Enum):
    """All possible sequencer events"""
    STEP_CHANGED = "step_changed"
    NOTE_TRIGGERED = "note_triggered"
    PLAY_STATE_CHANGED = "play_state_changed"
    BPM_CHANGED = "bpm_changed"
    TRACK_CHANGED = "track_changed"
    PATTERN_MODIFIED = "pattern_modified"
    TRACK_CHANNEL_CHANGED = "track_channel_changed"
    EXTERNAL_SYNC_CHANGED = "external_sync_changed"

@dataclass
class SequencerEvent:
    """Base event class"""
    event_type: EventType
    timestamp: float
    data: dict

class SequencerEventBus:
    """Pub/Sub event bus for sequencer events"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._all_subscribers: List[Callable] = []
    
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to specific event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable) -> None:
        """Subscribe to all events"""
        self._all_subscribers.append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from specific event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]
    
    def unsubscribe_all(self, callback: Callable) -> None:
        """Unsubscribe from all events"""
        self._all_subscribers = [cb for cb in self._all_subscribers if cb != callback]
    
    def publish(self, event: SequencerEvent) -> None:
        """Publish event to all subscribers"""
        import time
        event.timestamp = time.time()
        
        # Notify specific subscribers
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event subscriber: {e}")
        
        # Notify all-event subscribers
        for callback in self._all_subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in all-event subscriber: {e}")
```

### Step 1.3: Create UIAdapter Abstract Base Class

**File**: `adapters/ui_adapter.py`

```python
from abc import ABC, abstractmethod
from core.sequencer_event_bus import SequencerEvent, EventType
from typing import Optional

class UIAdapter(ABC):
    """Abstract base class for all UI implementations"""
    
    def __init__(self, sequencer_engine):
        """
        Initialize adapter with sequencer engine
        
        Args:
            sequencer_engine: SequencerEngine instance
        """
        self.sequencer = sequencer_engine
        self.is_running = False
        
        # Subscribe to all sequencer events
        self.sequencer.event_bus.subscribe_all(self.on_sequencer_event)
    
    # ===== Commands (UI → Sequencer) =====
    
    @abstractmethod
    def handle_play(self) -> None:
        """Handle play command"""
        pass
    
    @abstractmethod
    def handle_stop(self) -> None:
        """Handle stop command"""
        pass
    
    @abstractmethod
    def handle_note_input(self, track: int, step: int, note: int, velocity: int = 100) -> None:
        """Handle note input"""
        pass
    
    @abstractmethod
    def handle_note_delete(self, track: int, step: int) -> None:
        """Handle note deletion"""
        pass
    
    @abstractmethod
    def handle_set_bpm(self, bpm: int) -> None:
        """Handle BPM change"""
        pass
    
    @abstractmethod
    def handle_set_track(self, track: int) -> None:
        """Handle track selection"""
        pass
    
    # ===== Event Handlers (Sequencer → UI) =====
    
    @abstractmethod
    def on_sequencer_event(self, event: SequencerEvent) -> None:
        """
        Handle sequencer event
        
        This is called whenever the sequencer state changes.
        Adapters should update their UI based on the event.
        """
        pass
    
    @abstractmethod
    def render(self) -> None:
        """Render current UI state"""
        pass
    
    # ===== Lifecycle =====
    
    @abstractmethod
    def run(self) -> None:
        """Main event loop - should be blocking"""
        pass
    
    def shutdown(self) -> None:
        """Clean shutdown"""
        self.is_running = False
        self.sequencer.event_bus.unsubscribe_all(self.on_sequencer_event)
```

### Step 1.4: Create SequencerEngine (Core Logic)

**File**: `core/sequencer_engine.py`

This is the refactored `Sequencer` class with all UI dependencies removed:

```python
import time
import threading
from typing import List, Optional
from core.sequencer_state import SequencerState
from core.sequencer_event_bus import SequencerEventBus, SequencerEvent, EventType
from sequencer import Pattern, Note

class SequencerEngine:
    """
    Core sequencer logic with no UI dependencies.
    
    This class manages:
    - Pattern/track data
    - MIDI playback timing
    - State management
    - Event publishing
    """
    
    def __init__(self, midi_output, bpm: int = 120):
        self.midi_output = midi_output
        self._bpm = bpm
        self._tracks = [Pattern() for _ in range(8)]
        self._track_channels = [1] * 8
        self._is_playing = False
        self._current_step = 0
        self._current_track = 0
        self._external_sync = False
        
        # Threading
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._active_notes = set()
        
        # MIDI clock sync
        self._clock_count = 0
        self._last_clock_time = None
        self._clock_times = []
        
        # Event bus
        self.event_bus = SequencerEventBus()
        
        # Track ports and devices
        self._track_ports = {}
        self._track_devices = {}
    
    # ===== Properties (Read-only access) =====
    
    @property
    def bpm(self) -> int:
        return self._bpm
    
    @property
    def is_playing(self) -> bool:
        return self._is_playing
    
    @property
    def current_step(self) -> int:
        return self._current_step
    
    @property
    def current_track(self) -> int:
        return self._current_track
    
    @property
    def external_sync(self) -> bool:
        return self._external_sync
    
    # ===== State Queries =====
    
    def get_state(self) -> SequencerState:
        """Get immutable snapshot of current state"""
        return SequencerState(
            is_playing=self._is_playing,
            current_step=self._current_step,
            bpm=self._bpm,
            tracks=tuple(self._tracks),
            track_channels=tuple(self._track_channels),
            current_track=self._current_track,
            external_sync=self._external_sync
        )
    
    def get_track_notes(self, track: int) -> List[Note]:
        """Get all notes in a track"""
        if 0 <= track < len(self._tracks):
            return self._tracks[track].notes
        return []
    
    # ===== Commands (State-changing operations) =====
    
    def play(self) -> None:
        """Start playback"""
        if not self._is_playing:
            self._is_playing = True
            self._stop_event.clear()
            self._send_transport_to_active_devices('start')
            self._thread = threading.Thread(target=self._play_loop, daemon=True)
            self._thread.start()
            
            # Publish event
            self.event_bus.publish(SequencerEvent(
                event_type=EventType.PLAY_STATE_CHANGED,
                timestamp=0,
                data={'is_playing': True}
            ))
    
    def stop(self) -> None:
        """Stop playback"""
        if self._is_playing:
            self._is_playing = False
            self._stop_event.set()
            
            # Send note-off for all active notes
            for channel, note, port_name in self._active_notes:
                self.midi_output.send_note_off(channel, note, port_name)
            self._active_notes.clear()
            
            self._send_transport_to_active_devices('stop')
            if self._thread:
                self._thread.join()
            
            # Publish event
            self.event_bus.publish(SequencerEvent(
                event_type=EventType.PLAY_STATE_CHANGED,
                timestamp=0,
                data={'is_playing': False}
            ))
    
    def set_bpm(self, bpm: int) -> None:
        """Set tempo"""
        if self._bpm != bpm:
            self._bpm = max(1, min(300, bpm))
            self.event_bus.publish(SequencerEvent(
                event_type=EventType.BPM_CHANGED,
                timestamp=0,
                data={'bpm': self._bpm}
            ))
    
    def set_current_track(self, track: int) -> None:
        """Select active track"""
        if 0 <= track < 8 and self._current_track != track:
            self._current_track = track
            self.event_bus.publish(SequencerEvent(
                event_type=EventType.TRACK_CHANGED,
                timestamp=0,
                data={'track': track}
            ))
    
    def add_note(self, track: int, step: int, note: int, velocity: int = 100) -> None:
        """Add note to pattern"""
        if 0 <= track < len(self._tracks) and 0 <= step < 16:
            self._tracks[track].add_note(step, note, velocity)
            self.event_bus.publish(SequencerEvent(
                event_type=EventType.PATTERN_MODIFIED,
                timestamp=0,
                data={'track': track, 'step': step, 'note': note}
            ))
    
    def remove_note(self, track: int, step: int) -> None:
        """Remove note from pattern"""
        if 0 <= track < len(self._tracks):
            self._tracks[track].clear_step(step)
            self.event_bus.publish(SequencerEvent(
                event_type=EventType.PATTERN_MODIFIED,
                timestamp=0,
                data={'track': track, 'step': step, 'action': 'removed'}
            ))
    
    def set_track_channel(self, track: int, channel: int) -> None:
        """Set MIDI channel for track"""
        if 0 <= track < 8:
            self._track_channels[track] = max(1, min(16, channel))
            self.event_bus.publish(SequencerEvent(
                event_type=EventType.TRACK_CHANNEL_CHANGED,
                timestamp=0,
                data={'track': track, 'channel': channel}
            ))
    
    def set_track_port(self, track: int, port_name: str) -> None:
        """Set MIDI port for track"""
        self._track_ports[track] = port_name
    
    def set_track_device(self, track: int, device) -> None:
        """Set device for track"""
        self._track_devices[track] = device
    
    # ===== Internal Methods =====
    
    def _send_transport_to_active_devices(self, message_type: str) -> None:
        """Send start/stop to devices that want transport messages"""
        for track_idx, device in self._track_devices.items():
            if hasattr(device, 'send_transport') and device.send_transport:
                port_name = self._track_ports.get(track_idx)
                if message_type == 'start':
                    self.midi_output.send_start(port_name)
                elif message_type == 'stop':
                    self.midi_output.send_stop(port_name)
    
    def _play_loop(self) -> None:
        """Main playback loop"""
        step_duration = 60.0 / (self._bpm * 4)
        next_step_time = time.time()
        self.note_off_time = None
        self.current_step_notes = set()
        
        while not self._stop_event.is_set():
            current_time = time.time()
            
            # Send note-off for previous step
            if self.note_off_time and current_time >= self.note_off_time:
                for channel, note, port_name in self.current_step_notes:
                    self.midi_output.send_note_off(channel, note, port_name)
                    self._active_notes.discard((channel, note, port_name))
                self.current_step_notes.clear()
                self.note_off_time = None
            
            # Check if it's time for next step (internal timing only)
            if not self._external_sync and current_time >= next_step_time:
                self._trigger_step()
                next_step_time += step_duration
            
            time.sleep(0.01)
    
    def _trigger_step(self) -> None:
        """Trigger notes for current step"""
        # Send note-off for previous step
        for channel, note, port_name in self.current_step_notes:
            self.midi_output.send_note_off(channel, note, port_name)
            self._active_notes.discard((channel, note, port_name))
        self.current_step_notes.clear()
        
        # Play notes for all tracks at current step
        for track_idx, track_pattern in enumerate(self._tracks):
            notes_at_step = track_pattern.get_notes_at_step(self._current_step)
            
            for note in notes_at_step:
                channel = self._track_channels[track_idx]
                port_name = self._track_ports.get(track_idx)
                self.midi_output.send_note_on(channel, note.note, note.velocity, port_name)
                self._active_notes.add((channel, note.note, port_name))
                self.current_step_notes.add((channel, note.note, port_name))
        
        # Schedule note-off
        step_duration = 60.0 / (self._bpm * 4)
        self.note_off_time = time.time() + step_duration * 0.9
        
        # Advance step
        self._current_step = (self._current_step + 1) % 16
        
        # Publish event
        self.event_bus.publish(SequencerEvent(
            event_type=EventType.STEP_CHANGED,
            timestamp=0,
            data={'current_step': self._current_step}
        ))
    
    def handle_midi_clock(self) -> None:
        """Handle incoming MIDI clock"""
        current_time = time.time()
        self._clock_count += 1
        
        self.midi_output.send_clock()
        
        # Calculate BPM from clock timing
        if self._last_clock_time:
            self._clock_times.append(current_time - self._last_clock_time)
            if len(self._clock_times) > 24:
                self._clock_times.pop(0)
            
            if len(self._clock_times) >= 24:
                avg_interval = sum(self._clock_times) / len(self._clock_times)
                quarter_note_time = avg_interval * 24
                new_bpm = round(60.0 / quarter_note_time, 1)
                if abs(new_bpm - self._bpm) > 0.1:
                    self._bpm = new_bpm
        
        self._last_clock_time = current_time
        
        # Trigger step on every 6th clock
        if self._external_sync and self._is_playing and self._clock_count % 6 == 0:
            self._trigger_step()
    
    def handle_midi_start(self) -> None:
        """Handle incoming MIDI start"""
        self._clock_count = 0
        self._current_step = 0
        self._external_sync = True
        self.play()
    
    def handle_midi_stop(self) -> None:
        """Handle incoming MIDI stop"""
        self._external_sync = False
        self.stop()
```

### Step 1.5: Testing Phase 1

Create a simple test to verify the core abstraction works:

**File**: `tests/test_core_abstraction.py`

```python
import pytest
from core.sequencer_engine import SequencerEngine
from core.sequencer_event_bus import EventType
from midi_output import MidiOutput

def test_sequencer_engine_creation():
    """Test that SequencerEngine can be created"""
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    assert engine.bpm == 120
    assert engine.is_playing == False
    assert engine.current_step == 0

def test_sequencer_state_snapshot():
    """Test that state snapshots work"""
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    state = engine.get_state()
    assert state.bpm == 120
    assert state.is_playing == False

def test_event_bus_subscription():
    """Test that event bus works"""
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    
    events_received = []
    def on_event(event):
        events_received.append(event)
    
    engine.event_bus.subscribe(EventType.BPM_CHANGED, on_event)
    engine.set_bpm(140)
    
    assert len(events_received) == 1
    assert events_received[0].data['bpm'] == 140

def test_add_note():
    """Test adding notes"""
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    
    engine.add_note(0, 0, 60, 100)
    notes = engine.get_track_notes(0)
    assert len(notes) == 1
    assert notes[0].note == 60
```

---

## Summary of Phase 1

After completing Phase 1, you will have:

✅ **SequencerState**: Immutable state snapshots  
✅ **SequencerEventBus**: Pub/sub event system  
✅ **UIAdapter**: Abstract interface for all UIs  
✅ **SequencerEngine**: Pure sequencer logic with no UI dependencies  
✅ **Tests**: Verify core functionality works independently  

**Key Achievement**: The sequencer can now be tested and used without any UI framework.

---

## Next Phases (Brief Overview)

### Phase 2: Push2Adapter
Refactor current UI code into `Push2Adapter` that implements `UIAdapter`

### Phase 3: Refactor SequencerApp
Update `main.py` to use new architecture

### Phase 4: Example Implementations
Create web UI, CLI, etc. as examples

### Phase 5: Network Layer (Optional)
Add WebSocket/REST API for remote UIs

---

## Questions to Answer Before Proceeding

1. **Should I implement all phases at once, or incrementally?**
   - Recommended: Incrementally (test each phase)

2. **Do you want network support (web/iOS)?**
   - If yes, Phase 5 becomes critical
   - If no, focus on Phases 1-4

3. **Should I maintain backward compatibility?**
   - If yes, keep old code alongside new code during transition
   - If no, can refactor more aggressively

4. **Any specific UI implementations you want first?**
   - Push2 (current)
   - Web (Flask/React)
   - CLI (for testing)
   - iOS (future)

