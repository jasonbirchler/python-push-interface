import pytest
from unittest.mock import Mock, patch
from handlers.device_handler import DeviceHandler

class TestDeviceHandler:
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.device_selection_mode = False
        app.track_edit_mode = False
        app.held_track_button = None
        app.current_track = 0
        app.device_selection_index = 0
        app.encoder_accumulator = 0
        app.tracks = [None] * 8
        app.push = Mock()
        app.push.buttons = Mock()
        app.device_manager = Mock()
        app.midi_output = Mock()
        app.sequencer = Mock()
        app._update_track_buttons = Mock()
        app._init_cc_values_for_track = Mock()
        app._update_pad_colors = Mock()
        app.pad_states = {}
        return app
        
    def test_handle_add_track_enable_selection(self, mock_app):
        handler = DeviceHandler(mock_app)
        
        with patch('handlers.device_handler.push2_python.constants.BUTTON_UPPER_ROW_8', 'ok_btn'):
            with patch('handlers.device_handler.time.time', return_value=1000.0):
                handler.handle_add_track()
                
        assert mock_app.device_selection_mode is True
        mock_app.push.buttons.set_button_color.assert_called_with('ok_btn', 'white')
        
    def test_handle_add_track_disable_selection(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.device_selection_mode = True
        
        with patch('handlers.device_handler.push2_python.constants.BUTTON_UPPER_ROW_8', 'ok_btn'):
            handler.handle_add_track()
            
        assert mock_app.device_selection_mode is False
        
    def test_add_track_finds_empty_slot(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.tracks[0] = Mock()  # First track occupied
        
        with patch('handlers.device_handler.time.time', return_value=1000.0):
            handler._add_track()
            
        assert mock_app.current_track == 1  # Should select track 1
        assert mock_app.device_selection_mode is True
        assert mock_app.device_selection_index == 0
        assert mock_app.encoder_accumulator == 0
        
    def test_add_track_all_full(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.tracks = [Mock()] * 8  # All tracks occupied
        
        with patch('handlers.device_handler.push2_python.constants.BUTTON_ADD_TRACK', 'add_btn'):
            handler._add_track()
            
        mock_app.push.buttons.set_button_color.assert_called_with('add_btn', 'black')
        
    def test_handle_setup_valid_track(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.held_track_button = 2
        mock_app.tracks[2] = Mock()
        
        with patch.object(handler, '_enter_track_edit_mode') as mock_enter:
            handler.handle_setup()
            
        mock_enter.assert_called_once()
        
    def test_handle_setup_no_held_track(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.held_track_button = None
        
        with patch.object(handler, '_enter_track_edit_mode') as mock_enter:
            handler.handle_setup()
            
        mock_enter.assert_not_called()
        
    def test_handle_setup_empty_track(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.held_track_button = 2
        mock_app.tracks[2] = None
        
        with patch.object(handler, '_enter_track_edit_mode') as mock_enter:
            handler.handle_setup()
            
        mock_enter.assert_not_called()
        
    def test_handle_confirm_selection_success(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.device_selection_mode = True
        mock_device = Mock()
        mock_device.name = 'Test Device'
        mock_device.port = 'Test Port'
        mock_device.channel = 5
        mock_app.device_manager.get_device_by_index.return_value = mock_device
        mock_app.midi_output.connect.return_value = True
        
        handler.handle_confirm_selection()
        
        assert mock_app.tracks[0] == mock_device
        assert mock_app.device_selection_mode is False
        mock_app.sequencer.set_track_channel.assert_called_with(0, 5)
        mock_app.sequencer.set_track_port.assert_called_with(0, 'Test Port')
        mock_app._update_track_buttons.assert_called_once()
        
    def test_handle_confirm_selection_connection_failed(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.device_selection_mode = True
        mock_device = Mock()
        mock_app.device_manager.get_device_by_index.return_value = mock_device
        mock_app.midi_output.connect.return_value = False
        
        handler.handle_confirm_selection()
        
        assert mock_app.device_selection_mode is True  # Should stay in selection mode
        assert mock_app.tracks[0] is None  # Track not assigned
        
    def test_handle_confirm_selection_edit_mode(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.device_selection_mode = True
        mock_app.track_edit_mode = True
        mock_app.held_track_button = 3
        mock_device = Mock()
        mock_app.device_manager.get_device_by_index.return_value = mock_device
        mock_app.midi_output.connect.return_value = True
        
        handler.handle_confirm_selection()
        
        assert mock_app.tracks[3] == mock_device  # Should use held track button
        assert mock_app.track_edit_mode is False
        assert mock_app.held_track_button is None
        
    def test_enter_track_edit_mode(self, mock_app):
        handler = DeviceHandler(mock_app)
        mock_app.held_track_button = 2
        current_device = Mock()
        current_device.name = 'Current Device'
        current_device.port = 'Current Port'
        mock_app.tracks[2] = current_device
        
        # Mock device manager devices
        matching_device = Mock()
        matching_device.name = 'Current Device'
        matching_device.port = 'Current Port'
        mock_app.device_manager.current_devices = [Mock(), matching_device, Mock()]
        
        with patch('handlers.device_handler.push2_python.constants.BUTTON_UPPER_ROW_8', 'ok_btn'):
            with patch('handlers.device_handler.time.time', return_value=1000.0):
                handler._enter_track_edit_mode()
                
        assert mock_app.track_edit_mode is True
        assert mock_app.device_selection_mode is True
        assert mock_app.device_selection_index == 1  # Should find matching device at index 1
        mock_app.push.buttons.set_button_color.assert_called_with('ok_btn', 'white')