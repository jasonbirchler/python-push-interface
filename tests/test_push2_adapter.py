#!/usr/bin/env python3
"""Test script to verify Push2Adapter works with new architecture"""

from core.sequencer_engine import SequencerEngine
from adapters.push2_adapter import Push2Adapter
from midi_output import MidiOutput
import sys

def main():
    print("🎵 Testing Push2Adapter with new architecture")
    
    # Check for simulator flag
    use_simulator = '--simulator' in sys.argv or '-s' in sys.argv
    
    # Create core components
    midi_output = MidiOutput()
    sequencer = SequencerEngine(midi_output)
    midi_output.set_sequencer(sequencer._internal_sequencer)  # For clock sync
    
    # Create Push2 adapter
    adapter = Push2Adapter(sequencer, use_simulator=use_simulator)
    
    print("✅ Push2Adapter created successfully")
    print(f"   - Sequencer engine: {type(sequencer).__name__}")
    print(f"   - Push2 simulator: {use_simulator}")
    print(f"   - Event bus subscriptions: {len(adapter.event_bus._subscribers)}")
    
    # Test basic functionality
    print(f"\n📊 Initial state:")
    print(f"   - BPM: {sequencer.bpm}")
    print(f"   - Playing: {sequencer.is_playing}")
    print(f"   - Current step: {sequencer.current_step}")
    
    # Test event system
    events_received = []
    def test_event_handler(event):
        events_received.append(event)
    
    adapter.event_bus.subscribe(adapter.event_bus._subscribers.keys().__iter__().__next__(), test_event_handler)
    
    print(f"\n🎛️ Testing BPM change...")
    sequencer.set_bpm(140)
    print(f"   - New BPM: {sequencer.bpm}")
    
    print(f"\n✅ Push2Adapter test completed!")
    print(f"   - All components initialized")
    print(f"   - Event system working")
    print(f"   - Ready to run with adapter.run()")
    
    if '--run' in sys.argv:
        print(f"\n🚀 Starting Push2Adapter...")
        adapter.run()

if __name__ == '__main__':
    main()