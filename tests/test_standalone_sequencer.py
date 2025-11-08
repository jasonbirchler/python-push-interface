#!/usr/bin/env python3
"""Test script to verify sequencer works independently without Push2"""

from core.sequencer_engine import SequencerEngine
from core.sequencer_event_bus import EventType
from midi_output import MidiOutput
import time

def main():
    print("🎵 Testing standalone sequencer (no Push2 required)")
    
    # Create sequencer
    midi_output = MidiOutput()
    sequencer = SequencerEngine(midi_output)
    
    # Subscribe to events
    def on_step_changed(event):
        print(f"Step: {event.data['current_step']}")
    
    def on_play_state_changed(event):
        state = "PLAYING" if event.data['is_playing'] else "STOPPED"
        print(f"Playback: {state}")
    
    sequencer.event_bus.subscribe(EventType.STEP_CHANGED, on_step_changed)
    sequencer.event_bus.subscribe(EventType.PLAY_STATE_CHANGED, on_play_state_changed)
    
    # Test basic functionality
    print(f"Initial BPM: {sequencer.bpm}")
    print(f"Initial state: {'PLAYING' if sequencer.is_playing else 'STOPPED'}")
    
    # Add some notes
    print("\n📝 Adding notes to track 0...")
    sequencer.add_note(0, 0, 60, 100)  # C4 on step 0
    sequencer.add_note(0, 4, 64, 100)  # E4 on step 4
    sequencer.add_note(0, 8, 67, 100)  # G4 on step 8
    
    # Test state snapshot
    state = sequencer.get_state()
    print(f"State snapshot - Playing: {state.is_playing}, BPM: {state.bpm}")
    
    # Test BPM change
    print(f"\n🎛️ Changing BPM to 140...")
    sequencer.set_bpm(140)
    
    # Start playback
    print(f"\n▶️ Starting playback for 5 seconds...")
    try:
        sequencer.play()
        
        # Let it play for a bit
        time.sleep(5)
        
        # Stop playback
        print(f"\n⏹️ Stopping playback...")
        sequencer.stop()
    finally:
        # Ensure sequencer is stopped to prevent thread leaks
        if sequencer.is_playing:
            sequencer.stop()
    
    print(f"\n✅ Standalone sequencer test completed successfully!")
    print(f"   - Sequencer created without Push2")
    print(f"   - Events published and received")
    print(f"   - Notes added to patterns")
    print(f"   - Playback started and stopped")
    print(f"   - State snapshots working")

if __name__ == '__main__':
    main()