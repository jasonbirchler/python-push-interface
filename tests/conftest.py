import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_midi_output():
    """Mock MIDI output for testing"""
    mock = Mock()
    mock.output_ports = {}
    mock.available_ports = ['Test Port 1', 'Test Port 2']
    mock.clock_sources = ['Internal', 'Test Clock']
    mock.selected_clock_source = 'Internal'
    mock.connect.return_value = True
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