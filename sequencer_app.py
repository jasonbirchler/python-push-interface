import push2_python
import time
import sys
from sequencer import Sequencer
from midi_output import MidiOutput
from ui import SequencerUI
from device_manager import DeviceManager

class SequencerApp:
    def __init__(self, use_simulator=False):
        # Initialize components
        self.push = push2_python.Push2(run_simulator=use_simulator)
        self.midi_output = MidiOutput()
        self.device_manager = DeviceManager()
        self.sequencer = Sequencer(self.midi_output)
        self.ui = SequencerUI(self.sequencer, self.device_manager)
        self.ui.octave = 4  # Pass octave to UI
        self.held_step_pad = None
        self.octave = 4
        self.cc_values = {}  # Track CC values for current device
        self.last_encoder_time = 0  # Track when encoders were last used
        
        # Connect to first available MIDI port
        print(f"Available MIDI ports: {self.midi_output.available_ports}")
        if not self.midi_output.connect():
            print("Warning: No MIDI output connected")
        else:
            print(f"Connected to MIDI port: {self.midi_output.output_port.name if self.midi_output.output_port else 'None'}")
        print(f"Loaded {self.device_manager.get_device_count()} devices from {self.device_manager.config_file}")

        # Set up Push 2 event handlers
        self._setup_handlers()

        # Initialize with first device
        self._update_sequencer_for_device()

        # Set up pad color callback
        self.sequencer._update_pad_colors_callback = self._update_pad_colors

        # Pass CC values to UI
        self.ui.cc_values = self.cc_values
        self.ui.app_ref = self  # Give UI access to app for octave display

    def _setup_handlers(self):
        @push2_python.on_pad_pressed()
        def on_pad_pressed(push, pad_n, pad_ij, velocity):
            row, col = pad_ij
            # Bottom two rows for step sequencer (16 steps)
            if row >= 6:  # Bottom two rows
                step = (row - 6) * 8 + col  # Map to 0-15 (row 6 = steps 0-7, row 7 = steps 8-15)
                if step < 16:
                    self.held_step_pad = step
                    self._update_octave_buttons()
                    self._update_delete_button()
            # Top row for note input (12 notes)
            elif row == 0 and col < 12:
                if self.held_step_pad is not None:
                    note = 60 + (self.octave - 4) * 12 + col  # C + octave offset
                    print(f"Adding note {note} to step {self.held_step_pad}")
                    self.sequencer.pattern.add_note(self.held_step_pad, note, velocity)
                    self._update_pad_colors()

        @push2_python.on_pad_released()
        def on_pad_released(push, pad_n, pad_ij, velocity):
            row, col = pad_ij
            if row >= 6:  # Step sequencer pads
                step = (row - 6) * 8 + col  # Same mapping as press
                if step < 16 and step == self.held_step_pad:
                    self.held_step_pad = None
                    self._update_pad_colors()
                    self._update_octave_buttons()
                    self._update_delete_button()


        @push2_python.on_button_pressed()
        def on_button_pressed(push, button_name):
            print(f"Button pressed: {button_name}")  # Debug to see actual button names
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
            elif 'left' in button_name.lower():
                self.device_manager.prev_device()
                self._update_sequencer_for_device()
            elif 'right' in button_name.lower():
                self.device_manager.next_device()
                self._update_sequencer_for_device()
            elif 'octave' in button_name.lower() and 'up' in button_name.lower():
                self.octave = min(8, self.octave + 1)
                self.ui.octave = self.octave
                print(f"Octave up: {self.octave}")
            elif 'octave' in button_name.lower() and 'down' in button_name.lower():
                self.octave = max(1, self.octave - 1)
                self.ui.octave = self.octave
                print(f"Octave down: {self.octave}")
            elif 'delete' in button_name.lower() and self.held_step_pad is not None:
                if self.sequencer.pattern.get_notes_at_step(self.held_step_pad):
                    self.sequencer.pattern.clear_step(self.held_step_pad)
                    self._update_pad_colors()
                    print(f"Cleared step {self.held_step_pad}")
                
        @push2_python.on_encoder_rotated()
        def on_encoder_rotated(push, encoder_name, increment):

            if 'tempo' in encoder_name.lower():
                new_bpm = max(60, min(200, self.sequencer.bpm + increment))
                self.sequencer.set_bpm(new_bpm)
            elif 'master' in encoder_name.lower():
                new_channel = max(1, min(16, self.sequencer.midi_channel + increment))
                self.sequencer.set_midi_channel(new_channel)
            else:
                # Handle CC encoders - map Push encoder names to our encoder slots
                encoder_map = {
                    'Track1 Encoder': 'encoder_1', 'Track2 Encoder': 'encoder_2',
                    'Track3 Encoder': 'encoder_3', 'Track4 Encoder': 'encoder_4',
                    'Track5 Encoder': 'encoder_5', 'Track6 Encoder': 'encoder_6',
                    'Track7 Encoder': 'encoder_7', 'Track8 Encoder': 'encoder_8'
                }

                if encoder_name in encoder_map:
                    self._handle_cc_encoder(encoder_map[encoder_name], increment)
                else:
                    print(f"Unhandled encoder: {encoder_name}")  # Debug

    def _update_sequencer_for_device(self):
        device = self.device_manager.get_current_device()
        if device:
            self.sequencer.set_midi_channel(device.channel)
            # Connect to device's preferred MIDI port if available
            if device.port in self.midi_output.available_ports:
                self.midi_output.disconnect()
                self.midi_output.connect(device.port)
            # Initialize CC values for this device
            self._init_cc_values()
            # Update UI with new CC values
            self.ui.cc_values = self.cc_values

    def _init_cc_values(self):
        device = self.device_manager.get_current_device()
        if device:
            self.cc_values = {}
            cc_list = list(device.cc_mappings.items())[:8]  # First 8 CCs
            for i, (name, cc_num) in enumerate(cc_list):
                self.cc_values[f"encoder_{i+1}"] = {
                    "name": name,
                    "cc": cc_num,
                    "value": 64  # Default to middle value
                }
            print(f"Initialized {len(self.cc_values)} CC mappings: {list(self.cc_values.keys())}")  # Debug

    def _handle_cc_encoder(self, encoder_name, increment):
        if encoder_name in self.cc_values:
            cc_info = self.cc_values[encoder_name]
            new_value = max(0, min(127, cc_info["value"] + increment))
            cc_info["value"] = new_value

            # Send CC message
            print(f"Sending CC {cc_info['cc']} = {new_value} on channel {self.sequencer.midi_channel}")
            self.midi_output.send_cc(self.sequencer.midi_channel, cc_info["cc"], new_value)

            # Update UI reference and trigger fast display update
            self.ui.cc_values = self.cc_values
            self.last_encoder_time = time.time()

    def _update_pad_colors(self):
        # Update step sequencer pad colors (bottom 2 rows)
        for step in range(16):
            row = 6 + (step // 8)  # Row 6 for steps 0-7, row 7 for steps 8-15
            col = step % 8

            # Determine color based on state
            if step == self.sequencer.current_step and self.sequencer.is_playing:
                color = 'green'  # Current playing step
            elif self.sequencer.pattern.get_notes_at_step(step):
                color = 'orange'  # Step has notes
            else:
                color = 'white'  # Empty step

            self.push.pads.set_pad_color((row, col), color)

        # Update note input pads (top row, first 12 pads)
        for note_pad in range(12):
            if self.held_step_pad is not None:
                self.push.pads.set_pad_color((0, note_pad), 'blue')  # Available for input
            else:
                self.push.pads.set_pad_color((0, note_pad), 'white')  # Always visible

    def _update_octave_buttons(self):
        # Light up octave buttons when step pad is held
        try:
            if self.held_step_pad is not None:
                # Find octave button constants and light them up
                if hasattr(push2_python.constants, 'BUTTON_OCTAVE_UP'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_UP, 'white')
                if hasattr(push2_python.constants, 'BUTTON_OCTAVE_DOWN'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_DOWN, 'white')
            else:
                # Turn off octave buttons when no step pad held
                if hasattr(push2_python.constants, 'BUTTON_OCTAVE_UP'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_UP, 'black')
                if hasattr(push2_python.constants, 'BUTTON_OCTAVE_DOWN'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_DOWN, 'black')
        except Exception as e:
            print(f"Octave button update error: {e}")

    def _update_delete_button(self):
        # Light up delete button when holding step pad with existing note
        try:
            if (self.held_step_pad is not None and 
                self.sequencer.pattern.get_notes_at_step(self.held_step_pad)):
                if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, 'white')
            else:
                if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, 'black')
        except Exception as e:
            print(f"Delete button update error: {e}")



    def run(self):
        print("Sequencer app running...")
        print("Controls:")
        print("- Bottom 2 rows: Step sequencer pads (hold + note to add)")
        print("- Top row (first 12): Note input (C-B)")
        print("- Play button: Start/stop")
        print("- Left/Right arrows: Change device")
        print("- Octave up/down: Change octave")
        print("- Encoders: Adjust BPM/Channel")

        # Initialize button and pad colors after everything is set up
        time.sleep(1.0)  # Longer delay for Push hardware initialization
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')

        # Initialize pad colors after hardware is ready
        self._update_pad_colors()

        try:
            while True:
                # Check if encoders were used recently for faster updates
                current_time = time.time()
                if current_time - self.last_encoder_time < 2.0:  # Fast updates for 2 seconds after encoder use
                    update_interval = 0.1  # 10fps for responsive encoder feedback
                else:
                    update_interval = 1.0   # 1fps for normal operation

                # Update display
                frame = self.ui.get_current_frame()
                self.push.display.display_frame(frame, input_format=push2_python.constants.FRAME_FORMAT_RGB565)

                time.sleep(update_interval)

        except KeyboardInterrupt:
            print("Shutting down...")
            self.sequencer.stop()
            self.midi_output.disconnect()
