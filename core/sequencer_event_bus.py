from dataclasses import dataclass
from typing import Dict, List, Callable, Any
from enum import Enum

class EventType(Enum):
    """Sequencer event types"""
    STEP_CHANGED = "step_changed"
    NOTE_TRIGGERED = "note_triggered"
    PLAY_STATE_CHANGED = "play_state_changed"
    BPM_CHANGED = "bpm_changed"
    TRACK_CHANGED = "track_changed"
    PATTERN_MODIFIED = "pattern_modified"

@dataclass
class SequencerEvent:
    """Sequencer event data"""
    type: EventType
    data: Dict[str, Any]

class SequencerEventBus:
    """Pub/sub event system for sequencer"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, callback: Callable[[SequencerEvent], None]) -> None:
        """Subscribe to event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[SequencerEvent], None]) -> None:
        """Unsubscribe from event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    def publish(self, event: SequencerEvent) -> None:
        """Publish event to all subscribers"""
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event callback: {e}")