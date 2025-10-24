import push2_python
import time

class EncoderHandler:
    def __init__(self, app):
        self.app = app
        self._accumulators = {}  # Track accumulator for each encoder
        
    def _apply_encoder_threshold(self, encoder_key, increment, callback):
        """Apply encoder threshold logic and call callback when threshold is reached"""
        if encoder_key not in self._accumulators:
            self._accumulators[encoder_key] = 0
            
        self._accumulators[encoder_key] += increment
        
        if abs(self._accumulators[encoder_key]) >= self.app.encoder_threshold:
            direction = 1 if self._accumulators[encoder_key] > 0 else -1
            self._accumulators[encoder_key] = 0
            callback(direction)
        
    def handle_encoder_rotation(self, encoder_name, increment):
        """Route encoder rotations to appropriate handlers"""
        # Handle tempo encoder
        if encoder_name == push2_python.constants.ENCODER_TEMPO_ENCODER:
            self._handle_tempo_encoder(increment)
            return True
            
        # Handle device/channel selection encoders when in device selection mode
        if self.app.device_selection_mode:
            if encoder_name == push2_python.constants.ENCODER_TRACK1_ENCODER:
                self._handle_device_selection_encoder(increment)
                return True
            elif encoder_name == push2_python.constants.ENCODER_TRACK2_ENCODER:
                self._handle_channel_selection_encoder(increment)
                return True
                
        # Handle clock selection encoder when in clock selection mode
        if self.app.clock_selection_mode:
            if encoder_name == push2_python.constants.ENCODER_TRACK1_ENCODER:
                self._handle_clock_selection_encoder(increment)
                return True
                
        # Handle session project selection encoder when in session mode with open action
        if self.app.session_mode and self.app.session_action == 'open':
            if encoder_name == push2_python.constants.ENCODER_TRACK1_ENCODER:
                self._handle_session_project_encoder(increment)
                return True
                
        # Handle CC encoders (all 8 track encoders when not in device selection)
        track_encoders = {
            push2_python.constants.ENCODER_TRACK1_ENCODER: 'encoder_1',
            push2_python.constants.ENCODER_TRACK2_ENCODER: 'encoder_2',
            push2_python.constants.ENCODER_TRACK3_ENCODER: 'encoder_3',
            push2_python.constants.ENCODER_TRACK4_ENCODER: 'encoder_4',
            push2_python.constants.ENCODER_TRACK5_ENCODER: 'encoder_5',
            push2_python.constants.ENCODER_TRACK6_ENCODER: 'encoder_6',
            push2_python.constants.ENCODER_TRACK7_ENCODER: 'encoder_7',
            push2_python.constants.ENCODER_TRACK8_ENCODER: 'encoder_8',
        }
        
        if encoder_name in track_encoders and not self.app.device_selection_mode:
            self._handle_cc_encoder(track_encoders[encoder_name], increment)
            return True
            
        return False
        
    def _handle_tempo_encoder(self, increment):
        """Handle tempo encoder rotation"""
        new_bpm = max(60, min(200, self.app.sequencer.bpm + increment))
        if new_bpm != self.app.sequencer.bpm:
            self.app.sequencer.set_bpm(new_bpm)
            print(f"BPM: {new_bpm}")
            
    def _handle_device_selection_encoder(self, increment):
        """Handle device selection encoder"""
        def update_device_selection(direction):
            device_count = self.app.device_manager.get_device_count()
            if device_count > 0:
                self.app.device_selection_index = (self.app.device_selection_index + direction) % device_count
                self.app.last_encoder_time = time.time()
                
        self._apply_encoder_threshold('device_selection', increment, update_device_selection)
                
    def _handle_channel_selection_encoder(self, increment):
        """Handle MIDI channel selection encoder"""
        def update_channel(direction):
            if self.app.device_selection_mode:
                device = self.app.device_manager.get_device_by_index(self.app.device_selection_index)
                if device:
                    new_channel = max(1, min(16, device.channel + direction))
                    device.channel = new_channel
                    self.app.last_encoder_time = time.time()
                    
        self._apply_encoder_threshold('channel_selection', increment, update_channel)
                
    def _handle_clock_selection_encoder(self, increment):
        """Handle clock source selection encoder"""
        def update_clock_selection(direction):
            clock_count = len(self.app.midi_output.clock_sources)
            if clock_count > 0:
                self.app.clock_selection_index = (self.app.clock_selection_index + direction) % clock_count
                self.app.last_encoder_time = time.time()
                
        self._apply_encoder_threshold('clock_selection', increment, update_clock_selection)
            
    def _handle_cc_encoder(self, encoder_name, increment):
        """Handle CC encoder rotation"""
        if encoder_name in self.app.cc_values:
            cc_info = self.app.cc_values[encoder_name]
            
            def update_cc_value(direction):
                new_value = max(0, min(127, cc_info["value"] + direction))
                cc_info["value"] = new_value

                # Send CC message
                if self.app.tracks[self.app.current_track] is not None:
                    device = self.app.tracks[self.app.current_track]
                    self.app.midi_output.send_cc(device.channel, cc_info["cc"], new_value, device.port)

                # Update UI reference and trigger fast display update
                self.app.ui.cc_values = self.app.cc_values
                self.app.last_encoder_time = time.time()
                
            self._apply_encoder_threshold(f'cc_{encoder_name}', increment, update_cc_value)
            
    def _handle_session_project_encoder(self, increment):
        """Handle session project selection encoder"""
        def update_project_selection(direction):
            projects = self.app.project_manager.list_projects()
            if projects:
                project_count = len(projects)
                self.app.session_project_index = (self.app.session_project_index + direction) % project_count
                self.app.last_encoder_time = time.time()
                
        self._apply_encoder_threshold('session_project', increment, update_project_selection)