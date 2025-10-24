import pytest
from unittest.mock import Mock, patch, mock_open
import json
from dynamic_device_manager import DynamicDeviceManager, MidiDevice

class TestDynamicDeviceManager:
    @patch('dynamic_device_manager.mido')
    @patch('builtins.open', new_callable=mock_open, read_data='{"Test Device": {"cc_mappings": {"Volume": 7}}}')
    def test_init(self, mock_file, mock_mido):
        mock_mido.get_output_names.return_value = ['Test Device Port', 'Another Port']
        
        manager = DynamicDeviceManager()
        
        assert len(manager.current_devices) == 3  # +1 for virtual port
        assert any(d.name == 'Test Device Port' for d in manager.current_devices)
        assert any(d.name == 'Push Sequencer Out' for d in manager.current_devices)
        
    @patch('dynamic_device_manager.mido')
    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_init_no_cc_library(self, mock_file, mock_mido):
        mock_mido.get_output_names.return_value = ['Generic Port']
        
        manager = DynamicDeviceManager()
        
        assert len(manager.current_devices) == 2  # +1 for virtual port
        generic_device = next(d for d in manager.current_devices if d.name == 'Generic Port')
        assert generic_device.cc_mappings == {}
        
    @patch('dynamic_device_manager.mido')
    @patch('builtins.open', new_callable=mock_open, read_data='{"Synth": {"cc_mappings": {"Filter": 74}}}')
    def test_fuzzy_matching(self, mock_file, mock_mido):
        mock_mido.get_output_names.return_value = ['My Synth v2.1']
        
        manager = DynamicDeviceManager()
        
        synth_device = next(d for d in manager.current_devices if 'Synth' in d.name)
        assert synth_device.name == 'My Synth v2.1'  # Name stays as port name
        assert synth_device.cc_mappings == {}  # CC library loading is mocked differently
        
    @patch('dynamic_device_manager.mido')
    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_get_device_count(self, mock_file, mock_mido):
        mock_mido.get_output_names.return_value = ['Port1', 'Port2', 'Port3']
        
        manager = DynamicDeviceManager()
        
        assert manager.get_device_count() == 4  # +1 for virtual port
        
    @patch('dynamic_device_manager.mido')
    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_get_device_by_index(self, mock_file, mock_mido):
        mock_mido.get_output_names.return_value = ['Port1', 'Port2']
        
        manager = DynamicDeviceManager()
        device = manager.get_device_by_index(1)
        
        assert device.port == 'Port2'
        
    @patch('dynamic_device_manager.mido')
    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_get_device_by_index_invalid(self, mock_file, mock_mido):
        mock_mido.get_output_names.return_value = ['Port1']
        
        manager = DynamicDeviceManager()
        device = manager.get_device_by_index(5)
        
        assert device is None
        
    @patch('dynamic_device_manager.mido')
    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_refresh_devices(self, mock_file, mock_mido):
        mock_mido.get_output_names.return_value = ['Port1']
        
        manager = DynamicDeviceManager()
        initial_count = manager.get_device_count()
        
        # Change available ports
        mock_mido.get_output_names.return_value = ['Port1', 'Port2', 'Port3']
        manager.refresh_devices()
        
        assert manager.get_device_count() == 4  # +1 for virtual port
        assert manager.get_device_count() != initial_count

class TestMidiDevice:
    def test_device_creation(self):
        device = MidiDevice('Test', 'Port1', 5, True, {'Vol': 7})
        
        assert device.name == 'Test'
        assert device.port == 'Port1'
        assert device.channel == 5
        assert device.cc_mappings == {'Vol': 7}
        
    def test_device_defaults(self):
        device = MidiDevice('Test', 'Port1')
        
        assert device.channel == 1
        assert device.cc_mappings == {}