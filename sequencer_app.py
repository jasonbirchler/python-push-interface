import push2_python
import time
import sys
from sequencer import Sequencer
from midi_output import MidiOutput
from ui import SequencerUI

class SequencerApp:
    def __init__(self, use_simulator=False):
        # Initialize components
        self.push = push2_python.Push2(run_simulator=use_simulator)
        self.midi_output = MidiOutput()
        self.sequencer = Sequencer(self.midi_output)
        self.ui = SequencerUI(self.sequencer)
        
        # Connect to first available MIDI port
        print(f"Available MIDI ports: {self.midi_output.available_ports}")
        if not self.midi_output.connect():
            print("Warning: No MIDI output connected")
        else:
            print(f"Connected to MIDI port: {self.midi_output.output_port.name if self.midi_output.output_port else 'None'}")

        # Set up Push 2 event handlers
        self._setup_handlers()

        # Initialize button colors
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')

    def _setup_handlers(self):
        @push2_python.on_pad_pressed()
        def on_pad_pressed(push, pad_n, pad_ij, velocity):
            row, col = pad_ij
            # Bottom two rows for step selection (16 steps total)
            if row >= 6:  # Bottom two rows
                step = (7 - row) * 8 + col  # Map to 0-15
                if step < 16:
                    self.ui.selected_step = step
            # Top rows for note input
            elif row < 6:
                note = 60 + (5 - row) * 8 + col  # C4 + offset
                self.sequencer.pattern.add_note(self.ui.selected_step, note, velocity)


        @push2_python.on_button_pressed()
        def on_button_pressed(push, button_name):
            if button_name == 'play' or 'play' in button_name.lower():
                if self.sequencer.is_playing:
                    self.sequencer.stop()
                    push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')
                else:
                    self.sequencer.play()
                    push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'green')
            elif button_name == 'stop' or 'stop' in button_name.lower():
                self.sequencer.stop()
                self.sequencer.current_step = 0
                push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')
                
        @push2_python.on_encoder_rotated()
        def on_encoder_rotated(push, encoder_name, increment):

            if 'tempo' in encoder_name.lower():
                new_bpm = max(60, min(200, self.sequencer.bpm + increment))
                self.sequencer.set_bpm(new_bpm)
            elif 'master' in encoder_name.lower():
                new_channel = max(1, min(16, self.sequencer.midi_channel + increment))
                self.sequencer.set_midi_channel(new_channel)
                

                
    def run(self):
        print("Sequencer app running...")
        print("Controls:")
        print("- Bottom 2 rows: Select step (1-16)")
        print("- Top 6 rows: Add notes")
        print("- Play button: Start/stop")
        print("- Encoders: Adjust BPM/Channel (check debug output for names)")
        
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
    use_simulator = '--simulator' in sys.argv or '-s' in sys.argv
    app = SequencerApp(use_simulator=use_simulator)
    app.run()
