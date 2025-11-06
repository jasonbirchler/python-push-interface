#!/usr/bin/env python3
"""Main entry point using decoupled architecture"""

from core.sequencer_engine import SequencerEngine
from adapters.push2_adapter import Push2Adapter
from midi_output import MidiOutput
import sys

def main():
    use_simulator = '--simulator' in sys.argv or '-s' in sys.argv
    
    # Create core components
    midi_output = MidiOutput()
    sequencer = SequencerEngine(midi_output)
    midi_output.set_sequencer(sequencer._internal_sequencer)
    
    # Create UI adapter
    ui = Push2Adapter(sequencer, use_simulator=use_simulator)
    
    # Run the UI
    ui.run()

if __name__ == "__main__":
    main()