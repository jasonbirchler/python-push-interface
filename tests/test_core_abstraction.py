import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sequencer_engine import SequencerEngine
from core.sequencer_event_bus import EventType, SequencerEvent
from midi_output import MidiOutput

def test_sequencer_engine_creation():
    """Test sequencer engine can be created"""
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    assert engine.bpm == 120
    assert engine.is_playing == False
    assert engine.current_step == 0

def test_sequencer_state_snapshot():
    """Test state snapshots work"""
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    state = engine.get_state()
    assert state.bpm == 120
    assert state.is_playing == False
    assert state.current_step == 0

def test_event_bus_subscription():
    """Test event bus pub/sub works"""
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
    """Test adding notes works"""
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    
    engine.add_note(0, 0, 60, 100)
    notes = engine.get_track_notes(0)
    assert len(notes) > 0

def test_play_stop():
    """Test play/stop functionality"""
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    
    events_received = []
    def on_event(event):
        events_received.append(event)
    
    engine.event_bus.subscribe(EventType.PLAY_STATE_CHANGED, on_event)
    
    try:
        engine.play()
        assert engine.is_playing == True
        assert len(events_received) == 1
        assert events_received[0].data['is_playing'] == True
        
        engine.stop()
        assert engine.is_playing == False
        assert len(events_received) == 2
        assert events_received[1].data['is_playing'] == False
    finally:
        # Ensure sequencer is stopped to prevent thread leaks
        if engine.is_playing:
            engine.stop()

if __name__ == '__main__':
    test_sequencer_engine_creation()
    test_sequencer_state_snapshot()
    test_event_bus_subscription()
    test_add_note()
    test_play_stop()
    print("✅ All Phase 1 tests passed!")