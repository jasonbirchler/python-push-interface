"""Mock Push2 interface for testing and CI environments"""

from unittest.mock import Mock

class MockPush2:
    """Mock Push2 hardware interface"""
    def __init__(self, run_simulator=False):
        self.buttons = Mock()
        self.pads = Mock()
        self.display = Mock()
        self.run_simulator = run_simulator
        
        # Mock button methods
        self.buttons.set_button_color = Mock()
        self.buttons.set_all_buttons_color = Mock()
        
        # Mock pad methods
        self.pads.set_pad_color = Mock()
        self.pads.set_all_pads_to_black = Mock()
        
        # Mock display methods
        self.display.display_frame = Mock()

class MockConstants:
    """Mock Push2 constants"""
    # Button constants
    BUTTON_PLAY = 'BUTTON_PLAY'
    BUTTON_STOP = 'BUTTON_STOP'
    BUTTON_ADD_TRACK = 'BUTTON_ADD_TRACK'
    BUTTON_SETUP = 'BUTTON_SETUP'
    BUTTON_SESSION = 'BUTTON_SESSION'
    BUTTON_MUTE = 'BUTTON_MUTE'
    BUTTON_SOLO = 'BUTTON_SOLO'
    BUTTON_METRONOME = 'BUTTON_METRONOME'
    BUTTON_OCTAVE_UP = 'BUTTON_OCTAVE_UP'
    BUTTON_OCTAVE_DOWN = 'BUTTON_OCTAVE_DOWN'
    BUTTON_DELETE = 'BUTTON_DELETE'
    
    # Row buttons
    BUTTON_UPPER_ROW_1 = 'BUTTON_UPPER_ROW_1'
    BUTTON_UPPER_ROW_2 = 'BUTTON_UPPER_ROW_2'
    BUTTON_UPPER_ROW_3 = 'BUTTON_UPPER_ROW_3'
    BUTTON_UPPER_ROW_4 = 'BUTTON_UPPER_ROW_4'
    BUTTON_UPPER_ROW_5 = 'BUTTON_UPPER_ROW_5'
    BUTTON_UPPER_ROW_6 = 'BUTTON_UPPER_ROW_6'
    BUTTON_UPPER_ROW_7 = 'BUTTON_UPPER_ROW_7'
    BUTTON_UPPER_ROW_8 = 'BUTTON_UPPER_ROW_8'
    
    BUTTON_LOWER_ROW_1 = 'BUTTON_LOWER_ROW_1'
    BUTTON_LOWER_ROW_2 = 'BUTTON_LOWER_ROW_2'
    BUTTON_LOWER_ROW_3 = 'BUTTON_LOWER_ROW_3'
    BUTTON_LOWER_ROW_4 = 'BUTTON_LOWER_ROW_4'
    BUTTON_LOWER_ROW_5 = 'BUTTON_LOWER_ROW_5'
    BUTTON_LOWER_ROW_6 = 'BUTTON_LOWER_ROW_6'
    BUTTON_LOWER_ROW_7 = 'BUTTON_LOWER_ROW_7'
    BUTTON_LOWER_ROW_8 = 'BUTTON_LOWER_ROW_8'
    
    # Encoder constants
    ENCODER_TEMPO_ENCODER = 'ENCODER_TEMPO_ENCODER'
    ENCODER_TRACK1_ENCODER = 'ENCODER_TRACK1_ENCODER'
    ENCODER_TRACK2_ENCODER = 'ENCODER_TRACK2_ENCODER'
    ENCODER_TRACK3_ENCODER = 'ENCODER_TRACK3_ENCODER'
    ENCODER_TRACK4_ENCODER = 'ENCODER_TRACK4_ENCODER'
    ENCODER_TRACK5_ENCODER = 'ENCODER_TRACK5_ENCODER'
    ENCODER_TRACK6_ENCODER = 'ENCODER_TRACK6_ENCODER'
    ENCODER_TRACK7_ENCODER = 'ENCODER_TRACK7_ENCODER'
    ENCODER_TRACK8_ENCODER = 'ENCODER_TRACK8_ENCODER'
    
    # Animation constants
    ANIMATION_PULSING_QUARTER = 'ANIMATION_PULSING_QUARTER'
    
    # Display constants
    DISPLAY_LINE_PIXELS = 960
    DISPLAY_N_LINES = 160
    
    # Frame format constants
    FRAME_FORMAT_RGB565 = 'FRAME_FORMAT_RGB565'

# Mock decorator functions
def on_pad_pressed():
    def decorator(func):
        return func
    return decorator

def on_pad_released():
    def decorator(func):
        return func
    return decorator

def on_button_pressed():
    def decorator(func):
        return func
    return decorator

def on_button_released():
    def decorator(func):
        return func
    return decorator

def on_encoder_rotated():
    def decorator(func):
        return func
    return decorator

# Module-level exports
Push2 = MockPush2
constants = MockConstants()
