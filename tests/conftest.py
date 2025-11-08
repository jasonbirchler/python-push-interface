import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force mock MIDI usage in tests to avoid ALSA dependencies
@pytest.fixture(autouse=True)
def mock_mido():
    """Automatically mock mido for all tests to avoid ALSA dependencies"""
    # Import our comprehensive mocks
    import mock_midi
    import mock_push2
    
    with patch.dict('sys.modules', {
        'mido': mock_midi,
        'push2_python': mock_push2,
        'push2_python.constants': mock_push2.constants
    }):
        # Patch mido functions in midi_output
        with patch('midi_output.mido', mock_midi):
            with patch('midi_output.MIDI_AVAILABLE', False):
                yield

@pytest.fixture
def mock_midi_output():
    """Mock MIDI output for testing"""
    mock = Mock()
    mock.output_ports = {}
    mock.available_ports = ['Test Port 1', 'Test Port 2']
    mock.clock_sources = ['Internal', 'Test Clock']
    mock.selected_clock_source = 'Internal'
    mock.using_mock_midi = True
    mock.connect.return_value = True
    mock.send_note_on = Mock()
    mock.send_note_off = Mock()
    mock.send_cc = Mock()
    mock.send_start = Mock()
    mock.send_stop = Mock()
    mock.send_clock = Mock()
    return mock

@pytest.fixture
def mock_device_manager():
    """Mock device manager for testing"""
    mock = Mock()
    mock.current_devices = []
    mock.get_device_count.return_value = 2
    mock.get_device_by_index.return_value = Mock(name='Test Device', port='Test Port', channel=1, cc_mappings={})
    return mock

@pytest.fixture
def mock_push():
    """Mock Push2 hardware for testing"""
    mock = Mock()
    mock.buttons = Mock()
    mock.pads = Mock()
    mock.display = Mock()
    return mock

@pytest.fixture(autouse=True)
def cleanup_sequencers():
    """Automatically cleanup any running sequencers after each test"""
    # Store references to any sequencers created during test
    sequencers = []
    
    # Monkey patch Sequencer.__init__ to track instances
    original_init = None
    try:
        from sequencer import Sequencer
        original_init = Sequencer.__init__
        
        def tracking_init(self, *args, **kwargs):
            sequencers.append(self)
            return original_init(self, *args, **kwargs)
        
        Sequencer.__init__ = tracking_init
        
        yield  # Run the test
        
    finally:
        # Cleanup: stop all sequencers that might still be running
        for seq in sequencers:
            try:
                if hasattr(seq, 'is_playing') and seq.is_playing:
                    seq.stop()
            except:
                pass  # Ignore cleanup errors
        
        # Restore original __init__
        if original_init:
            Sequencer.__init__ = original_init