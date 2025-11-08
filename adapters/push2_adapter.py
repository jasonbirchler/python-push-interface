import push2_python
import time
import threading
from typing import Optional, List
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
        
        # New pad-based range selection state
        self.pressed_pads = {}  # Track currently pressed pads: {(row, col): timestamp}
        self.selected_range_start = 0  # First step in active range
        self.selected_range_end = 31   # Last step in active range (default full 32 steps)
        self.held_keyboard_pads = set()  # Currently held keyboard pads
        self.keyboard_octave_offset = 0  # Octave offset for keyboard
        self.keyboard_notes_c = set()  # C note positions on keyboard for highlighting
        self._init_keyboard_c_notes()
        self._init_piano_keyboard_layout()  # Initialize piano keyboard layout
        
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
        
        # Create range-aware note system
        self._setup_range_aware_note_system()
    
    def _init_keyboard_c_notes(self):
        """Initialize C note positions for keyboard highlighting"""
        # C notes are at positions where (note % 12) == 0
        # For the new piano layout, we'll highlight C notes differently
        self.keyboard_notes_c = set()
        
    def _init_piano_keyboard_layout(self):
        """Initialize piano keyboard layout mapping"""
        # Define which pads trigger notes
        # Rows 6 and 8: White keys (C-D-E-F-G-A-B-C)
        # Rows 5 and 7: Black keys (C#-D#-F#-G#-A#) with gaps at positions 0, 3, 7
        self.white_key_positions = set()
        self.black_key_positions = set()
        self.disabled_key_positions = set()
        
        # White keys: rows 5 and 7, all 8 columns
        for row in [5, 7]:  # Rows 6 and 8 in human terms
            for col in range(8):
                self.white_key_positions.add((row, col))
        
        # Black keys: rows 4 and 6, columns 0-7 but with gaps
        for row in [4, 6]:  # Rows 5 and 7 in human terms
            for col in range(8):
                # Gaps at 1st, 4th, 8th pads (0-indexed: positions 0, 3, 7)
                if col in [0, 3, 7]:
                    self.disabled_key_positions.add((row, col))
                else:
                    self.black_key_positions.add((row, col))
        
        # Map pad positions to note values for piano layout
        self.piano_note_mapping = {}
        
        # Define note mappings for each row
        # Row 7: C3 to C4 (white keys, bottom row)
        white_notes_row7 = [48, 50, 52, 53, 55, 57, 59, 60]  # C3-D3-E3-F3-G3-A3-B3-C4
        for col, note in enumerate(white_notes_row7):
            self.piano_note_mapping[(7, col)] = note
            
        # Row 5: C4 to C5 (white keys, middle row)
        white_notes_row5 = [60, 62, 64, 65, 67, 69, 71, 72]  # C4-D4-E4-F4-G4-A4-B4-C5
        for col, note in enumerate(white_notes_row5):
            self.piano_note_mapping[(5, col)] = note
            
        # Row 6: Black keys one octave lower (above row 7 white keys)
        black_notes_row6 = [49, 51, 54, 56, 58]  # C#3-D#3-F#3-G#3-A#3
        black_cols_row6 = [1, 2, 4, 5, 6]  # Skip positions 0, 3, 7
        for col, note in zip(black_cols_row6, black_notes_row6):
            self.piano_note_mapping[(6, col)] = note
            
        # Row 4: Black keys middle octave (above row 5 white keys)
        black_notes_row4 = [61, 63, 66, 68, 70]  # C#4-D#4-F#4-G#4-A#4
        black_cols_row4 = [1, 2, 4, 5, 6]  # Skip positions 0, 3, 7
        for col, note in zip(black_cols_row4, black_notes_row4):
            self.piano_note_mapping[(4, col)] = note
    
    def _setup_range_aware_note_system(self):
        """Setup range-aware note management that works at adapter level"""
        # Store original add_note method
        self._original_add_note = self.sequencer.add_note
        
        # Create range-aware version
        def range_aware_add_note(track, step, note, velocity):
            """Add note only if step is within active range"""
            if track == self.current_track:
                # Check if step is within active range
                if not self._is_step_in_active_range(step):
                    print(f"Ignoring note at step {step} (outside active range {self.selected_range_start}-{self.selected_range_end})")
                    return
                    
            # Call original add_note method
            return self._original_add_note(track, step, note, velocity)
        
        # Replace the add_note method
        self.sequencer.add_note = range_aware_add_note
        
        print(f"Range-aware note system installed. Active range: {self.selected_range_start}-{self.selected_range_end}")
    
    def _setup_event_handlers(self):
        """Subscribe to sequencer events"""
        self.event_bus.subscribe(EventType.STEP_CHANGED, self.on_step_changed)
        self.event_bus.subscribe(EventType.PLAY_STATE_CHANGED, self.on_play_state_changed)
        self.event_bus.subscribe(EventType.PATTERN_MODIFIED, self.on_pattern_modified)
        self.event_bus.subscribe(EventType.PATTERN_LENGTH_CHANGED, self.on_pattern_length_changed)
    
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
    
    def on_pattern_length_changed(self, event: SequencerEvent) -> None:
        """Handle pattern length change events"""
        track = event.data['track']
        length = event.data['length']
        print(f"Track {track} pattern length changed to {length}")
        self._update_pad_colors()
    
    def _setup_push2_handlers(self):
        """Setup Push2 event handlers"""
        @push2_python.on_pad_pressed()
        def on_pad_pressed(push, pad_n, pad_ij, velocity):
            row, col = pad_ij
            pad_id = (row, col)
            current_time = time.time()
            
            # Top 4 rows: Step sequencer (32 steps)
            if row < 4:
                step = row * 8 + col
                if step < 32:
                    # Track pressed pad for range selection
                    self.pressed_pads[pad_id] = current_time
                    
                    # Check for range selection (2 pads pressed within 200ms)
                    if len(self.pressed_pads) == 2:
                        self._process_range_selection()
                    else:
                        # Single pad press - toggle step selection
                        if self.held_step_pad == step:
                            # Deselect if same step pressed again
                            self.held_step_pad = None
                            print(f"Deselected step {step}")
                        else:
                            # Select new step for note input
                            self.held_step_pad = step
                            print(f"Selected step {step} for note input")
                        self._update_pad_colors()
            
            # Bottom 4 rows: MIDI keyboard (piano layout)
            else:
                # Check if this is a valid key position
                pad_pos = (row, col)
                
                # Skip disabled pads in black key rows
                if pad_pos in self.disabled_key_positions:
                    return  # Do nothing for disabled pads
                    
                if self.tracks[self.current_track] is not None:
                    # Calculate note based on piano layout mapping
                    if pad_pos in self.piano_note_mapping:
                        note = self.piano_note_mapping[pad_pos]
                        # Apply octave offset
                        note += self.keyboard_octave_offset * 12
                        note = max(0, min(127, note))  # Clamp to MIDI range
                    else:
                        # Fallback for any unmapped positions
                        base_note = 48 + self.keyboard_octave_offset * 12  # C3 base
                        note = base_note + (7 - row) * 8 + col
                        note = max(0, min(127, note))  # Clamp to MIDI range
                    
                    # Get track channel from sequencer
                    channel = self.sequencer._internal_sequencer.track_channels[self.current_track]
                    port_name = getattr(self.sequencer._internal_sequencer, '_track_ports', {}).get(self.current_track)
                    
                    # If step is selected, add note to sequencer
                    if self.held_step_pad is not None:
                        self.sequencer.add_note(self.current_track, self.held_step_pad, note, velocity)
                        print(f"Added keyboard note {note} to track {self.current_track} step {self.held_step_pad}")
                    
                    # Trigger note on device
                    self.midi_output.send_note_on(channel, note, velocity, port_name)
                    self.held_keyboard_pads.add(pad_id)
                    
                    # Schedule note off
                    threading.Timer(0.5, lambda: self._send_note_off(channel, note, port_name)).start()

        @push2_python.on_pad_released()
        def on_pad_released(push, pad_n, pad_ij, velocity):
            row, col = pad_ij
            pad_id = (row, col)
            
            # Top 4 rows: Step sequencer
            if row < 4:
                step = row * 8 + col
                if step < 32:
                    # Remove from pressed pads
                    if pad_id in self.pressed_pads:
                        del self.pressed_pads[pad_id]
                    
                    # Keep step selected - don't clear on release
            
            # Bottom 4 rows: MIDI keyboard
            else:
                # Check if this is a valid key position (not disabled)
                if pad_id not in self.disabled_key_positions:
                    if pad_id in self.held_keyboard_pads:
                        self.held_keyboard_pads.discard(pad_id)
            
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
                self.keyboard_octave_offset = min(5, self.keyboard_octave_offset + 1)
                print(f"Keyboard octave up: {self.keyboard_octave_offset}")
                
            case push2_python.constants.BUTTON_OCTAVE_DOWN:
                self.keyboard_octave_offset = max(-2, self.keyboard_octave_offset - 1)
                print(f"Keyboard octave down: {self.keyboard_octave_offset}")
                
            case push2_python.constants.BUTTON_DELETE:
                if (self.held_step_pad is not None and
                    self.tracks[self.current_track] is not None):
                    
                    # Check if step is within active range
                    if self._is_step_in_active_range(self.held_step_pad):
                        notes = self.sequencer._internal_sequencer.tracks[self.current_track].get_notes_at_step(self.held_step_pad)
                        if notes:
                            self.sequencer.remove_note(self.current_track, self.held_step_pad)
                            print(f"Cleared track {self.current_track} step {self.held_step_pad}")
                            self._update_pad_colors()
                    
            case push2_python.constants.BUTTON_UPPER_ROW_8:
                # OK Button - handle confirmations based on mode
                if self.clock_selection_mode:
                    self.button_manager.clock.handle_confirm_clock_selection()
                elif self.device_selection_mode or self.track_edit_mode:
                    self.button_manager.device.handle_confirm_selection()
                self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_8, DEFAULT_BUTTON_STATE)
    
    def _process_range_selection(self):
        """Process 2-pad press for range selection"""
        if len(self.pressed_pads) != 2:
            return
            
        # Get the two pressed pads
        pad_positions = list(self.pressed_pads.keys())
        pad1, pad2 = pad_positions[0], pad_positions[1]
        
        # Calculate step numbers
        step1 = pad1[0] * 8 + pad1[1]
        step2 = pad2[0] * 8 + pad2[1]
        
        # Determine range (first and last step)
        new_range_start = min(step1, step2)
        new_range_end = max(step1, step2)
        new_range_length = new_range_end - new_range_start + 1
        
        # Update UI range
        self.selected_range_start = new_range_start
        self.selected_range_end = new_range_end
        
        # Update sequencer pattern length AND range start to match UI range
        current_pattern_length = self.sequencer.get_pattern_length(self.current_track)
        current_range_start = getattr(self.sequencer._internal_sequencer, '_range_starts', {})[self.current_track] if self.current_track in getattr(self.sequencer._internal_sequencer, '_range_starts', {}) else 0
        
        if current_pattern_length != new_range_length or current_range_start != new_range_start:
            self.sequencer.set_pattern_length(self.current_track, new_range_length, new_range_start)
            print(f"Pattern updated: length {current_pattern_length}→{new_range_length}, range {current_range_start}→{new_range_start}")
        
        print(f"Range selection: steps {new_range_start} to {new_range_end}")
        print(f"Active range length: {new_range_length} steps")
        print(f"Sequencer pattern: length {self.sequencer.get_pattern_length(self.current_track)}, range start {current_range_start}")
        
        # Update visual feedback
        self._update_pad_colors()
        
        # Clear the pressed pads after processing
        self.pressed_pads.clear()
    
    def _send_note_off(self, channel, note, port_name):
        """Send note off message"""
        self.midi_output.send_note_off(channel, note, port_name)
    
    def _is_step_in_active_range(self, step):
        """Check if step is within the currently active range"""
        return self.selected_range_start <= step <= self.selected_range_end
    
    def _get_step_position(self, step):
        """Convert step number to (row, col) position on grid"""
        row = step // 8
        col = step % 8
        return (row, col)
    
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
        """Update pad colors with proper lighting system"""
        # Small delay to prevent rapid successive calls from causing ghost pads
        time.sleep(0.001)
        
        # Update top 4 rows: Step sequencer (32 steps)
        # All 32 pads should be lit - dim white outside range, full white/colors in range
        for row in range(4):
            for col in range(8):
                step = row * 8 + col
                pad_pos = (row, col)
                
                # Determine color based on range and state
                if self._is_step_in_active_range(step):
                    # Within active range - full brightness
                    if step == self.held_step_pad:
                        color = 'blue'  # Selected for note input
                    elif self._is_step_current(step):
                        color = 'green'  # Currently playing
                    elif (self.tracks[self.current_track] is not None and
                          self._has_notes_at_step(step)):
                        color = self.track_colors[self.current_track]  # Has notes
                    else:
                        color = 'white'  # Active but empty (full white)
                else:
                    # Outside active range - dim white
                    color = 'light_gray'  # Dim white for inactive range
                
                self.push.pads.set_pad_color(pad_pos, color)
        
        # Update bottom 4 rows: MIDI keyboard (piano layout)
        for row in range(4, 8):
            for col in range(8):
                pad_pos = (row, col)
                
                # Keyboard pad colors based on piano layout
                if pad_pos in self.disabled_key_positions:
                    color = 'dark_gray'  # Disabled pads
                elif pad_pos in self.held_keyboard_pads:
                    color = 'red'  # Currently playing
                elif (self.held_step_pad is not None and 
                      self.tracks[self.current_track] is not None and
                      self._is_note_at_step_and_pad(self.held_step_pad, pad_pos)):
                    color = 'blue'  # Note exists at selected step
                elif pad_pos in self.white_key_positions:
                    color = 'white'  # White keys
                elif pad_pos in self.black_key_positions:
                    color = 'turquoise'  # Black keys
                elif self.held_step_pad is not None and self.tracks[self.current_track] is not None:
                    color = 'light_gray'  # Ready for note input (fallback)
                else:
                    color = 'light_gray'  # Normal keyboard (fallback)
                
                self.push.pads.set_pad_color(pad_pos, color)
    
    def _is_step_current(self, step):
        """Check if step is currently playing for the active track"""
        if not self.sequencer.is_playing:
            return False
            
        # Map sequencer step to our adjusted step within the active range
        sequencer_step = self.sequencer.get_current_step(self.current_track)
        pattern_length = self.sequencer.get_pattern_length(self.current_track)
        
        # If the pattern length is different from active range, we need to map steps
        active_range_length = self.selected_range_end - self.selected_range_start + 1
        range_position = sequencer_step % active_range_length
        current_step_in_range = self.selected_range_start + range_position
        
        return current_step_in_range == step
    
    def _has_notes_at_step(self, step):
        """Check if there are notes at this step for the active track (range-aware)"""
        if self.tracks[self.current_track] is None:
            return False
        
        # Notes in the pattern are stored at their pattern-relative positions (0, 1, 2, etc.)
        # So we just need to check if there's a note at the given step in the pattern
        pattern = self.sequencer._internal_sequencer.tracks[self.current_track]
        notes = pattern.get_notes_at_step(step)
        
        # Handle both real notes and mock objects
        try:
            return len(notes) > 0
        except TypeError:
            # If notes is a mock object, check if it has notes
            return hasattr(notes, '__len__') and len(notes) > 0
    
    def _is_note_at_step_and_pad(self, step, pad_pos):
        """Check if a specific note exists at step that corresponds to keyboard pad"""
        if self.tracks[self.current_track] is None:
            return False
            
        # Get the MIDI note for this pad position
        if pad_pos in self.piano_note_mapping:
            pad_note = self.piano_note_mapping[pad_pos] + self.keyboard_octave_offset * 12
            pad_note = max(0, min(127, pad_note))  # Clamp to MIDI range
        else:
            return False
            
        # Get notes at this step
        pattern = self.sequencer._internal_sequencer.tracks[self.current_track]
        notes = pattern.get_notes_at_step(step)
        
        # Check if any note matches the pad's note
        try:
            for note in notes:
                if hasattr(note, 'note') and note.note == pad_note:
                    return True
        except (TypeError, AttributeError):
            pass
            
        return False
    
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
                self.tracks[self.current_track] is not None):
                
                # Check if step is within active range
                if self._is_step_in_active_range(self.held_step_pad):
                    notes = self.sequencer._internal_sequencer.tracks[self.current_track].get_notes_at_step(self.held_step_pad)
                    if notes:
                        if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                            self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, 'white')
                    else:
                        if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                            self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, DEFAULT_BUTTON_STATE)
                else:
                    if hasattr(push2_python.constants, 'BUTTON_DELETE'):
                        self.push.buttons.set_button_color(push2_python.constants.BUTTON_DELETE, DEFAULT_BUTTON_STATE)
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
                else:
                    # No existing project file, save as new
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    project_name = f"project_{timestamp}"
                    self.project_manager.save_project(project_name)
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
        print("- Bottom 4 rows: Piano-style keyboard (2 octaves)")
        print("- Rows 6,8: White keys (C-D-E-F-G-A-B-C)")
        print("- Rows 5,7: Black keys (C#-D#-F#-G#-A#) with gaps")
        print("- Play button: Start/stop all tracks")
        print("- Octave up/down: Change keyboard octave")
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
