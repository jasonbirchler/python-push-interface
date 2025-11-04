import push2_python
import time
from typing import Optional
from adapters.ui_adapter import UIAdapter
from core.sequencer_engine import SequencerEngine
from core.sequencer_event_bus import SequencerEvent, EventType
from dynamic_device_manager import DynamicDeviceManager
from project_manager import ProjectManager
from ui_main import SequencerUI
from handlers.button_manager import ButtonManager

DEFAULT_BUTTON_STATE = 'dark_gray'

class Push2Adapter(UIAdapter):
    """Push2 UI adapter implementation"""
    
    def __init__(self, sequencer: SequencerEngine, use_simulator=False):
        super().__init__(sequencer)
        
        # Initialize Push2 hardware
        self.push = push2_python.Push2(run_simulator=use_simulator)
        
        # Initialize components
        self.midi_output = sequencer.midi_output  # Reference to MIDI output
        self.device_manager = DynamicDeviceManager()
        self.project_manager = ProjectManager(self)
        self.ui = SequencerUI(sequencer._internal_sequencer, self.device_manager)
        
        # UI state
        self.held_step_pad = None
        self.octave = 4
        self.cc_values = {}
        self.last_encoder_time = 0
        self.tracks = [None] * 8
        self.track_colors = ['red', 'blue', 'yellow', 'purple', 'cyan', 'pink', 'orange', 'lime']
        self.current_track = 0
        self.device_selection_mode = False
        self.device_selection_index = 0
        self.last_step = -1
        self.encoder_accumulator = 0
        self.encoder_threshold = 1 if use_simulator else 13
        
        # Clock source selection
        self.clock_selection_mode = False
        self.clock_selection_index = 0
        
        # Session management
        self.session_mode = False
        self.session_action = None
        self.session_project_index = 0
        
        # Mute/Solo state
        self.track_muted = [False] * 8
        self.solo_mode = False
        self.soloed_track = None
        
        # Track editing state
        self.held_track_button = None
        self.track_edit_mode = False
        
        # Display refresh rates
        self.fast_refresh_rate = 0.02
        self.normal_refresh_rate = 0.5
        
        # Button constants
        self.UPPER_ROW_BUTTON_CONSTANTS = [
            'BUTTON_UPPER_ROW_1', 'BUTTON_UPPER_ROW_2', 'BUTTON_UPPER_ROW_3', 'BUTTON_UPPER_ROW_4',
            'BUTTON_UPPER_ROW_5', 'BUTTON_UPPER_ROW_6', 'BUTTON_UPPER_ROW_7', 'BUTTON_UPPER_ROW_8'
        ]
        self.LOWER_ROW_BUTTON_CONSTANTS = [
            'BUTTON_LOWER_ROW_1', 'BUTTON_LOWER_ROW_2', 'BUTTON_LOWER_ROW_3', 'BUTTON_LOWER_ROW_4',
            'BUTTON_LOWER_ROW_5', 'BUTTON_LOWER_ROW_6', 'BUTTON_LOWER_ROW_7', 'BUTTON_LOWER_ROW_8'
        ]
        
        # Initialize components
        self.device_manager.refresh_devices()
        self.ui.octave = self.octave
        self.ui.cc_values = self.cc_values
        self.ui.app_ref = self
        
        # Set app reference on internal sequencer for track audibility checks
        self.sequencer._internal_sequencer.app_ref = self
        
        # Set up pad color callback (like original implementation)
        self.sequencer._internal_sequencer._update_pad_colors_callback = self._update_pad_colors
        
        # Initialize button manager
        self.button_manager = ButtonManager(self)
        
        # Subscribe to sequencer events
        self._setup_event_handlers()
        
        # Setup Push2 handlers
        self._setup_push2_handlers()
    
    def _setup_event_handlers(self):
        """Subscribe to sequencer events"""
        self.event_bus.subscribe(EventType.STEP_CHANGED, self.on_step_changed)
        self.event_bus.subscribe(EventType.PLAY_STATE_CHANGED, self.on_play_state_changed)
        self.event_bus.subscribe(EventType.PATTERN_MODIFIED, self.on_pattern_modified)
    
    def on_sequencer_event(self, event: SequencerEvent) -> None:
        """Handle sequencer events (required by UIAdapter)"""
        # Events are handled by specific handlers above
        pass
    
    def on_step_changed(self, event: SequencerEvent) -> None:
        """Handle step change events"""
        self._update_pad_colors()
    
    def on_play_state_changed(self, event: SequencerEvent) -> None:
        """Handle play state change events"""
        self._update_pad_colors()

    def on_pattern_modified(self, event: SequencerEvent) -> None:
        """Handle pattern modification events"""
        self._update_pad_colors()
    
    def _setup_push2_handlers(self):
        """Setup Push2 event handlers"""
        @push2_python.on_pad_pressed()
        def on_pad_pressed(push, pad_n, pad_ij, velocity):
            row, col = pad_ij
            # Bottom two rows for step sequencer (16 steps)
            if row >= 6:  # Bottom two rows
                step = (row - 6) * 8 + col
                if step < 16:
                    self.held_step_pad = step
                    self._update_octave_buttons()
                    self._update_delete_button()
            # Top row for note input (12 notes)
            elif row == 0 and col < 12:
                if self.held_step_pad is not None and self.tracks[self.current_track] is not None:
                    note = 60 + (self.octave - 4) * 12 + col
                    print(f"Adding note {note} to track {self.current_track} step {self.held_step_pad}")
                    self.sequencer.add_note(self.current_track, self.held_step_pad, note, velocity)

        @push2_python.on_pad_released()
        def on_pad_released(push, pad_n, pad_ij, velocity):
            row, col = pad_ij
            if row >= 6:  # Step sequencer pads
                step = (row - 6) * 8 + col
                if step < 16 and step == self.held_step_pad:
                    self.held_step_pad = None
                    self._update_octave_buttons()
                    self._update_delete_button()
            
        @push2_python.on_button_released()
        def on_button_released(push, button_name):
            self.button_manager.handle_button_release(button_name)
                
        @push2_python.on_button_pressed()
        def on_button_pressed(push, button_name):
            if not self.button_manager.handle_button_press(button_name):
                self._handle_remaining_buttons(button_name)
                
        @push2_python.on_encoder_rotated()
        def on_encoder_rotated(push, encoder_name, increment):
            self.button_manager.handle_encoder_rotation(encoder_name, increment)
    
    def _handle_remaining_buttons(self, button_name):
        """Handle buttons not in button manager"""
        match button_name:
            case push2_python.constants.BUTTON_OCTAVE_UP:
                self.octave = min(8, self.octave + 1)
                self.ui.octave = self.octave
                print(f"Octave up: {self.octave}")
                
            case push2_python.constants.BUTTON_OCTAVE_DOWN:
                self.octave = max(1, self.octave - 1)
                self.ui.octave = self.octave
                print(f"Octave down: {self.octave}")
                
            case push2_python.constants.BUTTON_DELETE:
                if (self.held_step_pad is not None and 
                    self.tracks[self.current_track] is not None and 
                    self.sequencer._internal_sequencer.tracks[self.current_track].get_notes_at_step(self.held_step_pad)):
                    
                    self.sequencer.remove_note(self.current_track, self.held_step_pad)
                    print(f"Cleared track {self.current_track} step {self.held_step_pad}")
                    
            case push2_python.constants.BUTTON_UPPER_ROW_8:
                # OK Button - handle confirmations based on mode
                if self.clock_selection_mode:
                    self.button_manager.clock.handle_confirm_clock_selection()
                elif self.device_selection_mode or self.track_edit_mode:
                    self.button_manager.device.handle_confirm_selection()
                self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_8, DEFAULT_BUTTON_STATE)
    
    # UI state management methods (from original SequencerApp)
    def get_current_track_channel(self):
        """Get MIDI channel for current track"""
        if self.tracks[self.current_track] is not None:
            return self.tracks[self.current_track].channel
        return 1
    
    def _is_track_audible(self, track_idx):
        """Check if track should play notes based on mute/solo state"""
        if self.solo_mode:
            return track_idx == self.soloed_track
        else:
            return not self.track_muted[track_idx]
    
    def _update_track_buttons(self):
        """Update track button colors"""
        for i in range(8):
            if self.tracks[i] is not None:
                color = self.track_colors[i]
            else:
                color = DEFAULT_BUTTON_STATE
                
            button_name = self.LOWER_ROW_BUTTON_CONSTANTS[i]
            if hasattr(push2_python.constants, button_name):
                button_constant = getattr(push2_python.constants, button_name)
                self.push.buttons.set_button_color(button_constant, color)
    
    def _update_pad_colors(self):
        """Update pad colors based on current sequencer state"""
        # Small delay to prevent rapid successive calls from causing ghost pads
        time.sleep(0.001)
        
        # Clear all step sequencer pads first
        for row in range(6, 8):
            for col in range(8):
                self.push.pads.set_pad_color((row, col), 'black')
        
        # Set step pad colors
        for step in range(16):
            row = 6 + (step // 8)
            col = step % 8
            
            if step == self.sequencer.current_step and self.sequencer.is_playing:
                color = 'green'
            elif (self.tracks[self.current_track] is not None and
                  self.sequencer._internal_sequencer.tracks[self.current_track].get_notes_at_step(step)):
                color = self.track_colors[self.current_track]
            else:
                color = 'white'
                
            self.push.pads.set_pad_color((row, col), color)
        
        # Update note input pads
        for note_pad in range(12):
            if self.held_step_pad is not None and self.tracks[self.current_track] is not None:
                color = 'blue'
            else:
                color = 'white'
            self.push.pads.set_pad_color((0, note_pad), color)
    
    def _update_octave_buttons(self):
        """Update octave button colors"""
        try:
            if self.held_step_pad is not None:
                if hasattr(push2_python.constants, 'BUTTON_OCTAVE_UP'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_UP, 'white')
                if hasattr(push2_python.constants, 'BUTTON_OCTAVE_DOWN'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_DOWN, 'white')
            else:
                if hasattr(push2_python.constants, 'BUTTON_OCTAVE_UP'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_UP, DEFAULT_BUTTON_STATE)
                if hasattr(push2_python.constants, 'BUTTON_OCTAVE_DOWN'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_DOWN, DEFAULT_BUTTON_STATE)
        except Exception as e:
            print(f"Octave button update error: {e}")

    def _update_delete_button(self):
        """Update delete button color"""
        try:
            if (self.held_step_pad is not None and 
                self.tracks[self.current_track] is not None and
                self.sequencer._internal_sequencer.tracks[self.current_track].get_notes_at_step(self.held_step_pad)):
                if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, 'white')
            else:
                if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                    self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, DEFAULT_BUTTON_STATE)
        except Exception as e:
            print(f"Delete button update error: {e}")
    
    def _init_cc_values_for_track(self):
        """Initialize CC values for current track"""
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
    
    def _execute_session_action(self):
        """Execute the selected session action"""
        match self.session_action:
            case 'open':
                projects = self.project_manager.list_projects()
                if projects and 0 <= self.session_project_index < len(projects):
                    project_name = projects[self.session_project_index]
                    self.project_manager.load_project(project_name)
                    self.session_mode = False
                    self.session_action = None
            case 'save':
                if self.project_manager.current_project_file:
                    self.project_manager.save_project(self.project_manager.current_project_file)
                    self.session_mode = False
                    self.session_action = None
            case 'save_new':
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                project_name = f"project_{timestamp}"
                self.project_manager.save_project(project_name)
                self.session_mode = False
                self.session_action = None
    
    def run(self) -> None:
        """Start the Push2 UI event loop"""
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

        # Initialize button and pad colors
        time.sleep(1.0)
        self.push.buttons.set_all_buttons_color(DEFAULT_BUTTON_STATE)
        time.sleep(0.5)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_ADD_TRACK, 'white')

        # Init upper row buttons
        for i in range(8):
            button_name = self.UPPER_ROW_BUTTON_CONSTANTS[i]
            if hasattr(push2_python.constants, button_name):
                button_constant = getattr(push2_python.constants, button_name)
                self.push.buttons.set_button_color(button_constant, DEFAULT_BUTTON_STATE)

        # Initialize pad colors
        self._update_pad_colors()
        self._update_track_buttons()

        try:
            while True:
                # Adaptive refresh rate
                current_time = time.time()
                if (current_time - self.last_encoder_time < 2.0 or 
                    self.sequencer.is_playing or 
                    self.device_selection_mode):
                    update_interval = self.fast_refresh_rate
                else:
                    update_interval = self.normal_refresh_rate

                # Poll MIDI input for clock messages
                self.midi_output.poll_midi_input()
                
                # Update display
                frame = self.ui.get_current_frame()
                self.push.display.display_frame(frame, input_format=push2_python.constants.FRAME_FORMAT_RGB565)

                time.sleep(update_interval)

        except KeyboardInterrupt:
            print("Shutting down...")
            self.shutdown()
    
    def shutdown(self) -> None:
        """Cleanup resources"""
        self.sequencer.stop()
        self.midi_output.disconnect()
        self.push.pads.set_all_pads_to_black()
        self.push.buttons.set_all_buttons_color(DEFAULT_BUTTON_STATE)
