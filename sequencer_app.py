import push2_python
import time
from sequencer import Sequencer
from midi_output import MidiOutput
from ui import SequencerUI

class SequencerApp:
    def __init__(self):
        # Initialize components
        self.push = push2_python.Push2()
        self.midi_output = MidiOutput()
        self.sequencer = Sequencer(self.midi_output)
        self.ui = SequencerUI(self.sequencer)
        
        # Connect to first available MIDI port
        if not self.midi_output.connect():
            print("Warning: No MIDI output connected")
            
        # Set up Push 2 event handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        @push2_python.on_pad_pressed()
        def on_pad_pressed(push, pad_n, pad_ij, velocity):
            row, col = pad_ij
            if row == 1:  # Use bottom row for step selection
                self.ui.selected_step = col
            elif row == 0:  # Use top row for note input
                note = 60 + col  # C4 + offset
                self.sequencer.pattern.add_note(self.ui.selected_step, note, velocity)
                
        @push2_python.on_button_pressed()
        def on_button_pressed(push, button_name):
            if button_name == 'play':
                if self.sequencer.is_playing:
                    self.sequencer.stop()
                else:
                    self.sequencer.play()
            elif button_name == 'stop':
                self.sequencer.stop()
                self.sequencer.current_step = 0
                
        @push2_python.on_encoder_rotated()
        def on_encoder_rotated(push, encoder_name, increment):
            if encoder_name == 'tempo':
                new_bpm = max(60, min(200, self.sequencer.bpm + increment))
                self.sequencer.set_bpm(new_bpm)
            elif encoder_name == 'master':
                new_channel = max(1, min(16, self.sequencer.midi_channel + increment))
                self.sequencer.set_midi_channel(new_channel)
                
    def run(self):
        print("Sequencer app running...")
        print("Controls:")
        print("- Bottom row pads: Select step")
        print("- Top row pads: Add notes")
        print("- Play button: Start/stop")
        print("- Tempo encoder: Adjust BPM")
        print("- Master encoder: Change MIDI channel")
        
        try:
            while True:
                frame = self.ui.get_current_frame()
                self.push.display.display_frame(frame, input_format=push2_python.constants.FRAME_FORMAT_RGB565)
                time.sleep(1.0/30)  # 30fps
        except KeyboardInterrupt:
            print("Shutting down...")
            self.sequencer.stop()
            self.midi_output.disconnect()

if __name__ == "__main__":
    app = SequencerApp()
    app.run()