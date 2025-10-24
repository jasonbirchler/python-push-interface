import pytest
from unittest.mock import Mock, patch, MagicMock
from midi_output import MidiOutput

class TestMidiOutput:
    @patch('midi_output.mido')
    def test_init(self, mock_mido):
        mock_mido.get_output_names.return_value = ['Port1', 'Port2']
        mock_mido.get_input_names.return_value = ['Input1', 'Push 2']
        
        midi_output = MidiOutput()
        
        assert midi_output.available_ports == ['Port1', 'Port2']
        assert 'Internal' in midi_output.clock_sources
        assert 'Input1' in midi_output.clock_sources
        assert 'Push 2' not in midi_output.clock_sources  # Should be excluded
        
    @patch('midi_output.mido')
    def test_connect_exact_match(self, mock_mido):
        mock_mido.get_output_names.return_value = ['Test Port']
        mock_mido.get_input_names.return_value = []
        mock_port = Mock()
        mock_mido.open_output.return_value = mock_port
        
        midi_output = MidiOutput()
        result = midi_output.connect('Test Port')
        
        assert result is True
        assert 'Test Port' in midi_output.output_ports
        mock_mido.open_output.assert_called_with('Test Port')
        
    @patch('midi_output.mido')
    def test_connect_fuzzy_match(self, mock_mido):
        mock_mido.get_output_names.return_value = ['IAC Driver Bus 1']
        mock_mido.get_input_names.return_value = []
        mock_port = Mock()
        mock_mido.open_output.return_value = mock_port
        
        midi_output = MidiOutput()
        result = midi_output.connect('IAC Driver')
        
        assert result is True
        assert 'IAC Driver' in midi_output.output_ports
        mock_mido.open_output.assert_called_with('IAC Driver Bus 1')
        
    @patch('midi_output.mido')
    def test_send_note_on(self, mock_mido):
        mock_mido.get_output_names.return_value = ['Test Port']
        mock_mido.get_input_names.return_value = []
        mock_port = Mock()
        mock_mido.open_output.return_value = mock_port
        mock_message = Mock()
        mock_mido.Message.return_value = mock_message
        
        midi_output = MidiOutput()
        midi_output.connect('Test Port')
        midi_output.send_note_on(1, 60, 100)
        
        mock_mido.Message.assert_called_with('note_on', channel=0, note=60, velocity=100)
        mock_port.send.assert_called_with(mock_message)
        
    @patch('midi_output.mido')
    def test_send_note_off(self, mock_mido):
        mock_mido.get_output_names.return_value = ['Test Port']
        mock_mido.get_input_names.return_value = []
        mock_port = Mock()
        mock_mido.open_output.return_value = mock_port
        mock_message = Mock()
        mock_mido.Message.return_value = mock_message
        
        midi_output = MidiOutput()
        midi_output.connect('Test Port')
        midi_output.send_note_off(1, 60)
        
        mock_mido.Message.assert_called_with('note_off', channel=0, note=60, velocity=0)
        mock_port.send.assert_called_with(mock_message)
        
    @patch('midi_output.mido')
    def test_send_cc(self, mock_mido):
        mock_mido.get_output_names.return_value = ['Test Port']
        mock_mido.get_input_names.return_value = []
        mock_port = Mock()
        mock_mido.open_output.return_value = mock_port
        mock_message = Mock()
        mock_mido.Message.return_value = mock_message
        
        midi_output = MidiOutput()
        midi_output.connect('Test Port')
        midi_output.send_cc(1, 7, 64)
        
        mock_mido.Message.assert_called_with('control_change', channel=0, control=7, value=64)
        mock_port.send.assert_called_with(mock_message)
        
    @patch('midi_output.mido')
    @patch('midi_output.platform.system')
    def test_select_clock_source_macos(self, mock_platform, mock_mido):
        mock_platform.return_value = 'Darwin'
        mock_mido.get_output_names.return_value = []
        mock_mido.get_input_names.return_value = ['Test Clock']
        
        midi_output = MidiOutput()
        midi_output.select_clock_source('Test Clock')
        
        assert midi_output.selected_clock_source == 'Test Clock'
        # Should not open input port on macOS
        mock_mido.open_input.assert_not_called()
        
    @patch('midi_output.mido')
    @patch('midi_output.platform.system')
    def test_select_clock_source_linux(self, mock_platform, mock_mido):
        mock_platform.return_value = 'Linux'
        mock_mido.get_output_names.return_value = []
        mock_mido.get_input_names.return_value = ['Test Clock']
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        midi_output = MidiOutput()
        midi_output.select_clock_source('Test Clock')
        
        assert midi_output.selected_clock_source == 'Test Clock'
        mock_mido.open_input.assert_called_with('Test Clock')
        assert mock_port.callback == midi_output._handle_midi_message
        
    @patch('midi_output.mido')
    def test_handle_midi_message_with_sequencer(self, mock_mido):
        mock_mido.get_output_names.return_value = []
        mock_mido.get_input_names.return_value = []
        
        midi_output = MidiOutput()
        mock_sequencer = Mock()
        midi_output.set_sequencer(mock_sequencer)
        
        # Test clock message
        clock_msg = Mock(type='clock')
        midi_output._handle_midi_message(clock_msg)
        mock_sequencer.handle_midi_clock.assert_called_once()
        
        # Test start message
        start_msg = Mock(type='start')
        midi_output._handle_midi_message(start_msg)
        mock_sequencer.handle_midi_start.assert_called_once()
        
        # Test stop message
        stop_msg = Mock(type='stop')
        midi_output._handle_midi_message(stop_msg)
        mock_sequencer.handle_midi_stop.assert_called_once()