import push2_python
from .transport_handler import TransportHandler
from .track_handler import TrackHandler
from .device_handler import DeviceHandler
from .clock_handler import ClockHandler

class ButtonManager:
    def __init__(self, app):
        self.app = app
        self.transport = TransportHandler(app)
        self.track = TrackHandler(app)
        self.device = DeviceHandler(app)
        self.clock = ClockHandler(app)
        
    def handle_button_press(self, button_name):
        """Route button presses to appropriate handlers"""
        print(f"Button pressed: '{button_name}'")
        
        # Track selection buttons
        if 'Lower Row' in button_name:
            try:
                track_num = int(button_name.split()[-1]) - 1
                if 0 <= track_num < 8 and self.app.tracks[track_num] is not None:
                    self.track.handle_track_selection(track_num)
            except (ValueError, IndexError):
                print(f"Invalid track button: {button_name}")
            return
            
        # Route other buttons
        button_handlers = {
            push2_python.constants.BUTTON_PLAY: self.transport.handle_play,
            push2_python.constants.BUTTON_STOP: self.transport.handle_stop,
            push2_python.constants.BUTTON_MUTE: self.track.handle_mute,
            push2_python.constants.BUTTON_SOLO: self.track.handle_solo,
            push2_python.constants.BUTTON_ADD_TRACK: self.device.handle_add_track,
            push2_python.constants.BUTTON_SETUP: self.device.handle_setup,
            push2_python.constants.BUTTON_METRONOME: self.clock.handle_metronome_button,
        }
        
        handler = button_handlers.get(button_name)
        if handler:
            handler()
        else:
            # Handle remaining buttons in app (octave, session, etc.)
            return False  # Indicates button not handled
        return True  # Indicates button was handled
        
    def handle_button_release(self, button_name):
        """Handle button releases"""
        if 'Lower Row' in button_name:
            self.track.handle_track_release()
            
    def handle_encoder_rotation(self, encoder_name, increment):
        """Route encoder rotations to appropriate handlers"""
        # Handle tempo encoder
        if encoder_name == push2_python.constants.ENCODER_TEMPO_ENCODER:
            self.transport.handle_tempo_encoder(increment)
            return True
            
        # Handle device/channel selection encoders when in device selection mode
        if self.app.device_selection_mode:
            if encoder_name == push2_python.constants.ENCODER_TRACK1_ENCODER:
                self.device.handle_device_selection_encoder(increment)
                return True
            elif encoder_name == push2_python.constants.ENCODER_TRACK2_ENCODER:
                self.device.handle_channel_selection_encoder(increment)
                return True
                
        # Handle clock selection encoder when in clock selection mode
        if self.app.clock_selection_mode:
            if encoder_name == push2_python.constants.ENCODER_TRACK1_ENCODER:
                self.clock.handle_clock_selection_encoder(increment)
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
            self.app._handle_cc_encoder(track_encoders[encoder_name], increment)
            return True
            
        return False  # Indicates encoder not handled
