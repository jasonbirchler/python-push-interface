#!/usr/bin/env python3
"""Integration tests for the new decoupled architecture"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch
from core.sequencer_engine import SequencerEngine
from adapters.push2_adapter import Push2Adapter
from core.sequencer_event_bus import EventType
from midi_output import MidiOutput
import time

def test_integration():
    """Test full integration of new architecture"""
    print("🧪 Running integration tests...")
    
    # Create components
    midi_output = MidiOutput()
    sequencer = SequencerEngine(midi_output)
    
    # Mock Push2Adapter to avoid hardware dependencies in CI
    with patch('adapters.push2_adapter.push2_python') as mock_push2:
        mock_push2.Push2.return_value = Mock()
        adapter = Push2Adapter(sequencer, use_simulator=True)
    
    # Test 1: Components created successfully
    assert sequencer is not None
    assert adapter is not None
    assert adapter.sequencer == sequencer
    print("✅ Test 1: Components created")
    
    # Test 2: Event system working
    events_received = []
    def capture_event(event):
        events_received.append(event)
    
    adapter.event_bus.subscribe(EventType.BPM_CHANGED, capture_event)
    sequencer.set_bpm(140)
    
    assert len(events_received) == 1
    assert events_received[0].data['bpm'] == 140
    print("✅ Test 2: Event system working")
    
    # Test 3: Sequencer functionality
    sequencer.add_note(0, 0, 60, 100)
    notes = sequencer.get_track_notes(0)
    assert len(notes) > 0
    print("✅ Test 3: Sequencer functionality")
    
    # Test 4: Play/stop with events
    events_received.clear()
    adapter.event_bus.subscribe(EventType.PLAY_STATE_CHANGED, capture_event)
    
    try:
        sequencer.play()
        assert sequencer.is_playing == True
        time.sleep(0.1)  # Allow event to propagate
        
        sequencer.stop()
        assert sequencer.is_playing == False
        print("✅ Test 4: Play/stop with events")
    finally:
        # Ensure sequencer is stopped to prevent thread leaks
        if sequencer.is_playing:
            sequencer.stop()
    
    # Test 5: UI state management
    assert adapter.current_track == 0
    assert adapter.octave == 4
    assert len(adapter.tracks) == 8
    print("✅ Test 5: UI state management")
    
    # Test 6: Push2 components initialized
    assert adapter.push is not None
    assert adapter.device_manager is not None
    assert adapter.project_manager is not None
    print("✅ Test 6: Push2 components initialized")
    
    print("🎉 All integration tests passed!")

def test_feature_parity():
    """Test that key features from original are preserved"""
    print("🔍 Testing feature parity...")
    
    midi_output = MidiOutput()
    sequencer = SequencerEngine(midi_output)
    
    # Mock Push2Adapter to avoid hardware dependencies in CI
    with patch('adapters.push2_adapter.push2_python') as mock_push2:
        mock_push2.Push2.return_value = Mock()
        adapter = Push2Adapter(sequencer, use_simulator=True)
    
    # Test multi-track support
    assert len(adapter.tracks) == 8
    assert len(adapter.track_colors) == 8
    print("✅ Multi-track support")
    
    # Test mute/solo state
    assert len(adapter.track_muted) == 8
    assert adapter.solo_mode == False
    print("✅ Mute/solo state")
    
    # Test device selection
    assert adapter.device_selection_mode == False
    assert adapter.device_selection_index == 0
    print("✅ Device selection")
    
    # Test session management
    assert adapter.session_mode == False
    assert adapter.session_action is None
    print("✅ Session management")
    
    # Test octave control
    assert adapter.octave == 4
    print("✅ Octave control")
    
    print("🎉 Feature parity tests passed!")

if __name__ == '__main__':
    try:
        test_integration()
        test_feature_parity()
        print("\n🏆 ALL TESTS PASSED - New architecture is ready!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)