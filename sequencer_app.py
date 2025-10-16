import push2_python
import time
import sys
from sequencer import Sequencer
from midi_output import MidiOutput
from ui import SequencerUI
from dynamic_device_manager import DynamicDeviceManager
from project_manager import ProjectManager

class SequencerApp:
    def __init__(self, use_simulator=False):
        # Initialize components
        self.push = push2_python.Push2(run_simulator=use_simulator)
        self.midi_output = MidiOutput()
        self.device_manager = DynamicDeviceManager()
        self.sequencer = Sequencer(self.midi_output)
        self.midi_output.set_sequencer(self.sequencer)  # Enable clock sync
        self.project_manager = ProjectManager(self)
        self.ui = SequencerUI(self.sequencer, self.device_manager)
        self.ui.octave = 4  # Pass octave to UI
        self.held_step_pad = None
        self.octave = 4
        self.cc_values = {}  # Track CC values for current device
        self.last_encoder_time = 0  # Track when encoders were last used
        self.tracks = [None] * 8  # Track assignments (None = empty, device = assigned)
        self.track_colors = ['red', 'blue', 'yellow', 'purple', 'cyan', 'pink', 'orange', 'lime']  # Colors for tracks 0-7
        self.current_track = 0
        self.device_selection_mode = False
        self.device_selection_index = 0
        self.pad_states = {}  # Track current pad colors to avoid unnecessary updates
        self.last_step = -1  # Track last step to minimize updates
        self.encoder_accumulator = 0  # Accumulate encoder increments for device selection
        self.encoder_threshold = 13  # num of increments required before encoder changes value
        
        # Clock source selection
        self.clock_selection_mode = False
        self.clock_selection_index = 0
        self.metronome_button_held = False
        
        # Project selection
        self.project_selection_mode = False
        self.project_selection_index = 0
        self.browse_button_held = False
        
        # Session management
        self.session_mode = False
        self.session_action = None  # 'open', 'save', 'save_new'
        self.session_project_index = 0

        # Display refresh rate configuration
        # shorter values means less time between cycles or faster refresh
        # i.e. 1/rate = fps
        self.fast_refresh_rate = 0.02  # for active use (encoders, device selection, playback)
        self.normal_refresh_rate = 0.5  # for idle state

        self.UPPER_ROW_BUTTON_CONSTANTS = [
            'BUTTON_UPPER_ROW_1', 'BUTTON_UPPER_ROW_2', 'BUTTON_UPPER_ROW_3', 'BUTTON_UPPER_ROW_4',
            'BUTTON_UPPER_ROW_5', 'BUTTON_UPPER_ROW_6', 'BUTTON_UPPER_ROW_7', 'BUTTON_UPPER_ROW_8'
        ]
        self.LOWER_ROW_BUTTON_CONSTANTS = [
            'BUTTON_LOWER_ROW_1', 'BUTTON_LOWER_ROW_2', 'BUTTON_LOWER_ROW_3', 'BUTTON_LOWER_ROW_4',
            'BUTTON_LOWER_ROW_5', 'BUTTON_LOWER_ROW_6', 'BUTTON_LOWER_ROW_7', 'BUTTON_LOWER_ROW_8'
        ]
        
        # Refresh device manager to include virtual port
        self.device_manager.refresh_devices()
        
        # Connect to first available MIDI port
        print(f"Available MIDI ports: {self.midi_output.available_ports}")
        if not self.midi_output.connect():
            print("Warning: No MIDI output connected")
        else:
            print(f"Connected to MIDI port: {list(self.midi_output.output_ports.keys())}")
        print(f"Found {self.device_manager.get_device_count()} MIDI ports, CC library: {self.device_manager.cc_library_file}")

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
                if self.held_step_pad is not None and self.tracks[self.current_track] is not None:
                    note = 60 + (self.octave - 4) * 12 + col  # C + octave offset
                    print(f"Adding note {note} to track {self.current_track} step {self.held_step_pad}")
                    self.sequencer.tracks[self.current_track].add_note(self.held_step_pad, note, velocity)
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
            
        @push2_python.on_button_released()
        def on_button_released(push, button_name):
            if button_name == push2_python.constants.BUTTON_METRONOME:
                if self.clock_selection_mode:
                    self._confirm_clock_selection()
                self.metronome_button_held = False
                self.clock_selection_mode = False

                
        @push2_python.on_button_pressed()
        def on_button_pressed(push, button_name):
            print(f"Button pressed: '{button_name}'")  # Debug to see actual button names

            if button_name == push2_python.constants.BUTTON_PLAY:
                if self.sequencer.is_playing:
                    self.sequencer.stop()
                    push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')
                else:
                    self.sequencer.play()
                    push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'green', push2_python.constants.ANIMATION_PULSING_QUARTER)
            elif button_name == push2_python.constants.BUTTON_STOP:
                self.sequencer.stop()
                self.sequencer.current_step = 0
                push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')
            elif button_name == push2_python.constants.BUTTON_LEFT:
                self.device_manager.prev_device()
                self._update_sequencer_for_device()
            elif button_name == push2_python.constants.BUTTON_RIGHT:
                self.device_manager.next_device()
                self._update_sequencer_for_device()
            elif button_name == push2_python.constants.BUTTON_OCTAVE_UP:
                self.octave = min(8, self.octave + 1)
                self.ui.octave = self.octave
                print(f"Octave up: {self.octave}")
            elif button_name == push2_python.constants.BUTTON_OCTAVE_DOWN:
                self.octave = max(1, self.octave - 1)
                self.ui.octave = self.octave
                print(f"Octave down: {self.octave}")
            elif button_name == push2_python.constants.BUTTON_DELETE and self.held_step_pad is not None:
                if (self.tracks[self.current_track] is not None and 
                    self.sequencer.tracks[self.current_track].get_notes_at_step(self.held_step_pad)):
                    self.sequencer.tracks[self.current_track].clear_step(self.held_step_pad)
                    self._update_pad_colors()
                    print(f"Cleared track {self.current_track} step {self.held_step_pad}")
            elif button_name == push2_python.constants.BUTTON_ADD_TRACK:
                print(f"Add track button detected: {button_name}")
                self._add_track()
            elif button_name == push2_python.constants.BUTTON_SELECT:
                print(f"Select button detected: {button_name}")
                if self.device_selection_mode:
                    self._confirm_device_selection()
            elif button_name == push2_python.constants.BUTTON_METRONOME:
                self.metronome_button_held = True
                self.clock_selection_mode = True
                self.clock_selection_index = 0
                print("Clock source selection mode")
                self.last_encoder_time = time.time()
            elif button_name == push2_python.constants.BUTTON_SESSION:
                # Toggle session management mode
                self.session_mode = not self.session_mode
                if self.session_mode:
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_SESSION, 'white')
                    self.session_action = None
                    print("Session mode")

                    # Light up Open, Save, Save New buttons
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_1, 'white')
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_2, 'white')
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_3, 'white')
                    
                    self.last_encoder_time = time.time()
                else:
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_SESSION, 'dark_gray')
                    print("Exiting session mode")
            elif 'Upper Row' in button_name and self.session_mode:
                # Handle upper row buttons in session mode
                match button_name:
                    case push2_python.constants.BUTTON_UPPER_ROW_1:  # Open
                        self.session_action = 'open'
                        self.session_project_index = 0

                        # Light up OK button
                        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_8, 'white')

                        print("Session: Open project")
                    case push2_python.constants.BUTTON_UPPER_ROW_2:  # Save
                        # Light up OK button
                        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_8, 'white')

                        self.session_action = 'save'
                        print("Session: Save project")
                    case push2_python.constants.BUTTON_UPPER_ROW_3:  # Save New
                        self.session_action = 'save_new'
                        print("Session: Save new project")
                    case push2_python.constants.BUTTON_UPPER_ROW_8:  # OK
                        self._execute_session_action()
                        
                        # Turn off ok LED
                        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_8, 'white')
                    case _:
                        print(f"Invalid session button: {button_name}")
            elif button_name == push2_python.constants.BUTTON_USER:
                # Quick save (old behavior for compatibility)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"project_{timestamp}"
                self.project_manager.save_project(filename)
            elif 'Lower Row' in button_name:
                # Track selection buttons (Lower Row 1-8)
                try:
                    track_num = int(button_name.split()[-1]) - 1  # Convert to 0-based index
                    if 0 <= track_num < 8 and self.tracks[track_num] is not None:
                        self.current_track = track_num
                        print(f"Selected track {track_num}")
                        self._update_track_buttons()
                        self._init_cc_values_for_track()
                        # Force pad update when switching tracks
                        self.pad_states = {}
                        self._update_pad_colors()
                except (ValueError, IndexError):
                    print(f"Invalid track button: {button_name}")
                
        @push2_python.on_encoder_rotated()
        def on_encoder_rotated(push, encoder_name, increment):

            match encoder_name:
                case push2_python.constants.ENCODER_TEMPO_ENCODER:
                    new_bpm = max(60, min(200, self.sequencer.bpm + increment))
                    self.sequencer.set_bpm(new_bpm)
                
                case push2_python.constants.ENCODER_MASTER_ENCODER:
                    if self.device_selection_mode:
                        # Accumulate encoder increments for more natural feel
                        self.encoder_accumulator += increment
                        threshold = self.encoder_threshold
                        
                        if abs(self.encoder_accumulator) >= threshold:
                            device_count = self.device_manager.get_device_count()
                            direction = 1 if self.encoder_accumulator > 0 else -1
                            self.device_selection_index = (self.device_selection_index + direction) % device_count
                            self.encoder_accumulator = 0  # Reset accumulator
                            print(f"Device selection: {self.device_selection_index}")
                
                case push2_python.constants.ENCODER_SWING_ENCODER:
                    if self.clock_selection_mode:
                        # Clock source selection
                        self.encoder_accumulator += increment
                        threshold = self.encoder_threshold
                        
                        if abs(self.encoder_accumulator) >= threshold:
                            clock_count = len(self.midi_output.clock_sources)
                            direction = 1 if self.encoder_accumulator > 0 else -1
                            self.clock_selection_index = (self.clock_selection_index + direction) % clock_count
                            self.encoder_accumulator = 0
                            print(f"Clock selection: {self.midi_output.clock_sources[self.clock_selection_index]}")
                            self.last_encoder_time = time.time()
                
                case push2_python.constants.ENCODER_TRACK1_ENCODER:
                    if self.session_mode and self.session_action == 'open':
                        # Project browsing in session mode
                        self.encoder_accumulator += increment
                        threshold = self.encoder_threshold
                        
                        if abs(self.encoder_accumulator) >= threshold:
                            projects = self.project_manager.list_projects()
                            if projects:
                                project_count = len(projects)
                                direction = 1 if self.encoder_accumulator > 0 else -1
                                self.session_project_index = (self.session_project_index + direction) % project_count
                                self.encoder_accumulator = 0
                                print(f"Session project: {projects[self.session_project_index]}")
                                self.last_encoder_time = time.time()

    def _update_sequencer_for_device(self):
        # This method is no longer needed for multi-track, but keeping for compatibility
        pass

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
            if self.tracks[self.current_track] is not None:
                device = self.tracks[self.current_track]
                print(f"Sending CC {cc_info['cc']} = {new_value} on channel {device.channel} port {device.port}")
                self.midi_output.send_cc(device.channel, cc_info["cc"], new_value, device.port)

            # Update UI reference and trigger fast display update
            self.ui.cc_values = self.cc_values
            self.last_encoder_time = time.time()

    def _add_track(self):
        print("_add_track called")
        # Find next empty track slot
        for i in range(8):
            if self.tracks[i] is None:
                self.current_track = i
                self.device_selection_mode = True
                self.device_selection_index = 0
                self.encoder_accumulator = 0  # Reset accumulator
                print(f"Adding track {i}, select device... (device_selection_mode = {self.device_selection_mode})")
                self._update_track_buttons()
                # Force UI update to show device selection
                self.last_encoder_time = time.time()
                return
        print("All tracks are full")
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_ADD_TRACK, 'black')
        
    def _confirm_device_selection(self):
        if self.device_selection_mode:
            device = self.device_manager.get_device_by_index(self.device_selection_index)
            if device:
                # Try to connect to device port first
                if self.midi_output.connect(device.port):
                    self.tracks[self.current_track] = device
                    self.sequencer.set_track_channel(self.current_track, device.channel)
                    self.sequencer.set_track_port(self.current_track, device.port)
                    self.sequencer.set_track_device(self.current_track, device)
                    self.device_selection_mode = False
                    print(f"Track {self.current_track} assigned to {device.name} on port {device.port}")
                    self._update_track_buttons()
                    self._init_cc_values_for_track()
                    # Force pad update after confirming device
                    self.pad_states = {}
                    self._update_pad_colors()
                else:
                    print(f"Failed to connect to {device.name} - track not assigned")
                    # Stay in device selection mode to try another device
                
    def _init_cc_values_for_track(self):
        if self.tracks[self.current_track] is not None:
            device = self.tracks[self.current_track]
            self.cc_values = {}
            cc_list = list(device.cc_mappings.items())[:8]
            for i, (name, cc_num) in enumerate(cc_list):
                self.cc_values[f"encoder_{i+1}"] = {
                    "name": name,
                    "cc": cc_num,
                    "value": 64
                }
            self.ui.cc_values = self.cc_values
            
    def _confirm_clock_selection(self):
        """Confirm clock source selection"""
        if self.clock_selection_mode:
            selected_source = self.midi_output.clock_sources[self.clock_selection_index]
            self.midi_output.select_clock_source(selected_source)
            print(f"Clock source selected: {selected_source}")
            self.clock_selection_mode = False
            
    def _execute_session_action(self):
        """Execute the selected session action"""
        match self.session_action:
            case 'open':
                projects = self.project_manager.list_projects()
                if projects:
                    selected_project = projects[self.session_project_index]
                    self.project_manager.load_project(selected_project)
                    print(f"Project loaded: {selected_project}")
            case 'save':
                if self.project_manager.current_project_file:
                    # Save to existing file
                    self.project_manager.save_project(self.project_manager.current_project_file)
                else:
                    # Save as new file
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"project_{timestamp}"
                    self.project_manager.save_project(filename)
            case 'save_new':
                # Always save as new file
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"project_{timestamp}"
                self.project_manager.save_project(filename)
        
        # Exit session mode after action
        self.session_mode = False
        self.session_action = None
            
    def _update_track_buttons(self):
        # Update track buttons (Lower Row 1-8)
        
        for i in range(8):
            if self.tracks[i] is not None:
                color = self.track_colors[i]  # Assigned track (track color)
            else:
                color = 'black'  # Empty track
                
            # Set the actual button color
            button_name = self.LOWER_ROW_BUTTON_CONSTANTS[i]
            if hasattr(push2_python.constants, button_name):
                button_constant = getattr(push2_python.constants, button_name)
                self.push.buttons.set_button_color(button_constant, color)
            else:
                print(f"Button constant {button_name} not found")
            
    def _update_pad_colors(self):
        # Only update if step changed or forced update
        if self.sequencer.is_playing and self.last_step == self.sequencer.current_step:
            return  # Skip update if step hasn't changed
            
        self.last_step = self.sequencer.current_step
        
        # Clear all pads first (only if not initialized)
        if not self.pad_states:
            for row in range(8):
                for col in range(8):
                    self.push.pads.set_pad_color((row, col), 'black')
                    self.pad_states[(row, col)] = 'black'
        
        # Update step sequencer pad colors (rows 6-7 only)
        for step in range(16):
            row = 6 + (step // 8)  # Row 6 for steps 0-7, row 7 for steps 8-15
            col = step % 8

            # Determine color based on state (priority order)
            if step == self.sequencer.current_step and self.sequencer.is_playing:
                color = 'green'  # Current playing step (highest priority)
            elif (self.tracks[self.current_track] is not None and
                  self.sequencer.tracks[self.current_track].get_notes_at_step(step)):
                color = self.track_colors[self.current_track]  # Step has notes (track color)
            else:
                color = 'white'  # Empty step

            # Only update if color changed
            if self.pad_states.get((row, col)) != color:
                self.push.pads.set_pad_color((row, col), color)
                self.pad_states[(row, col)] = color

        # Update note input pads (row 0, first 12 pads only)
        for note_pad in range(12):
            if self.held_step_pad is not None and self.tracks[self.current_track] is not None:
                color = 'blue'  # Available for input
            else:
                color = 'white'  # Always visible
                
            # Only update if color changed
            if self.pad_states.get((0, note_pad)) != color:
                self.push.pads.set_pad_color((0, note_pad), color)
                self.pad_states[(0, note_pad)] = color

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
                self.tracks[self.current_track] is not None and
                self.sequencer.tracks[self.current_track].get_notes_at_step(self.held_step_pad)):
                if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, 'white')
            else:
                if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, 'black')
        except Exception as e:
            print(f"Delete button update error: {e}")



    def run(self):
        print("Multi-Track Sequencer running...")
        print("Controls:")
        print("- Add Track button: Create new track")
        print("- Track buttons (1-8): Select active track")
        print("- Master encoder: Browse devices (when adding track)")
        print("- Select button: Confirm device selection")
        print("- Bottom 2 rows: Step sequencer (16 steps)")
        print("- Top row (first 12): Note input (C-B)")
        print("- Play button: Start/stop all tracks")
        print("- Octave up/down: Change octave")
        print("- Track encoders: Adjust CCs for current track")

        # Initialize button and pad colors after everything is set up
        time.sleep(1.0)  # Longer delay for Push hardware initialization
        self.push.buttons.set_all_buttons_color('dark_gray')
        time.sleep(0.5)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_ADD_TRACK, 'white')

        # Init upper row buttons
        for i in range(8):
            button_name = self.UPPER_ROW_BUTTON_CONSTANTS[i]
            if hasattr(push2_python.constants, button_name):
                button_constant = getattr(push2_python.constants, button_name)
                self.push.buttons.set_button_color(button_constant, 'black')

        # Initialize pad colors after hardware is ready
        self._update_pad_colors()
        self._update_track_buttons()

        try:
            while True:
                # Check if encoders were used recently or sequencer is playing for faster updates
                current_time = time.time()
                if (current_time - self.last_encoder_time < 2.0 or 
                    self.sequencer.is_playing or 
                    self.device_selection_mode):
                    update_interval = self.fast_refresh_rate
                else:
                    update_interval = self.normal_refresh_rate

                # Update display
                frame = self.ui.get_current_frame()
                self.push.display.display_frame(frame, input_format=push2_python.constants.FRAME_FORMAT_RGB565)

                time.sleep(update_interval)

        except KeyboardInterrupt:
            print("Shutting down...")
            self.sequencer.stop()
            self.midi_output.disconnect()
            self.push.pads.set_all_pads_to_black()
            self.push.buttons.set_all_buttons_color('black')
