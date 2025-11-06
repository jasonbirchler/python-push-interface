import pytest
from unittest.mock import Mock, patch
from sequencer import Sequencer

class TestSequencerTransport:
    """Tests for sequencer transport message functionality with device assignment"""
    
    @pytest.fixture
    def mock_midi_output(self):
        mock = Mock()
        mock.send_start = Mock()
        mock.send_stop = Mock()
        mock.send_note_on = Mock()
        mock.send_note_off = Mock()
        return mock
    
    @pytest.fixture
    def mock_device(self):
        device = Mock()
        device.send_transport = True
        device.name = "Test Device"
        device.port = "Test Port"
        return device
    
    def test_sequencer_starts_with_transport_device(self, mock_midi_output, mock_device):
        """Test that sequencer can start after assigning a device with send_transport=True"""
        sequencer = Sequencer(mock_midi_output)
        
        try:
            # Assign a device to track 0 (simulating device assignment)
            sequencer.set_track_device(0, mock_device)
            sequencer.set_track_port(0, "Test Port")
            
            # This should not raise an exception
            sequencer.play()
            
            # Verify sequencer started
            assert sequencer.is_playing
            
            # Verify transport message was sent (without port parameter)
            mock_midi_output.send_start.assert_called_once_with()
        finally:
            # Always stop the sequencer to clean up the thread
            if sequencer.is_playing:
                sequencer.stop()
        
    def test_sequencer_stops_after_device_assignment(self, mock_midi_output, mock_device):
        """Test that sequencer can stop after assigning a device with send_transport=True"""
        sequencer = Sequencer(mock_midi_output)
        
        try:
            # Assign a device and start sequencer
            sequencer.set_track_device(0, mock_device)
            sequencer.set_track_port(0, "Test Port")
            sequencer.play()
            
            # This should not raise an exception
            sequencer.stop()
            
            # Verify sequencer stopped
            assert not sequencer.is_playing
            
            # Verify transport messages were sent (without port parameter)
            mock_midi_output.send_start.assert_called_once_with()
            mock_midi_output.send_stop.assert_called_once_with()
        finally:
            # Ensure sequencer is stopped
            if sequencer.is_playing:
                sequencer.stop()
        
    def test_sequencer_ignores_devices_without_send_transport(self, mock_midi_output):
        """Test that devices without send_transport=True don't receive transport messages"""
        sequencer = Sequencer(mock_midi_output)
        
        try:
            # Create device without send_transport
            device = Mock()
            device.send_transport = False
            device.name = "No Transport Device"
            
            sequencer.set_track_device(0, device)
            sequencer.set_track_port(0, "Test Port")
            
            sequencer.play()
            sequencer.stop()
            
            # Verify no transport messages were sent
            mock_midi_output.send_start.assert_not_called()
            mock_midi_output.send_stop.assert_not_called()
        finally:
            # Ensure sequencer is stopped
            if sequencer.is_playing:
                sequencer.stop()
        
    def test_sequencer_handles_missing_send_transport_attribute(self, mock_midi_output):
        """Test that devices without send_transport attribute don't cause errors"""
        sequencer = Sequencer(mock_midi_output)
        
        try:
            # Create device without send_transport attribute at all
            device = Mock()
            del device.send_transport  # Remove the attribute
            device.name = "Legacy Device"
            
            sequencer.set_track_device(0, device)
            sequencer.set_track_port(0, "Test Port")
            
            # This should not raise an exception
            sequencer.play()
            sequencer.stop()
            
            # Verify no transport messages were sent
            mock_midi_output.send_start.assert_not_called()
            mock_midi_output.send_stop.assert_not_called()
        finally:
            # Ensure sequencer is stopped
            if sequencer.is_playing:
                sequencer.stop()