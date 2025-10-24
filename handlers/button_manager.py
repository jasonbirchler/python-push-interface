import push2_python
from .transport_handler import TransportHandler
from .track_handler import TrackHandler
from .device_handler import DeviceHandler
from .clock_handler import ClockHandler
from .encoder_handler import EncoderHandler

class ButtonManager:
    def __init__(self, app):
        self.app = app
        self.transport = TransportHandler(app)
        self.track = TrackHandler(app)
        self.device = DeviceHandler(app)
        self.clock = ClockHandler(app)
        self.encoder = EncoderHandler(app)
        
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
        """Route encoder rotations to encoder handler"""
        return self.encoder.handle_encoder_rotation(encoder_name, increment)
