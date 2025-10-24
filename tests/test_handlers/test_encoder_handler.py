import pytest
from unittest.mock import Mock, patch
from handlers.encoder_handler import EncoderHandler

class TestEncoderHandler:
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.sequencer = Mock()
        app.sequencer.bpm = 120
        app.device_selection_mode = False
        app.clock_selection_mode = False
        app.encoder_accumulator = 0
        app.encoder_threshold = 13
        app.device_manager = Mock()
        app.device_manager.get_device_count.return_value = 3
        app.device_selection_index = 0
        app.clock_selection_index = 0
        app.midi_output = Mock()
        app.midi_output.clock_sources = ['Internal', 'Clock1', 'Clock2']
        app.current_track = 0
        app.tracks = [None] * 8
        app.cc_values = {'encoder_1': {'cc': 7, 'value': 64}}
        app.ui = Mock()
        return app
        
    def test_tempo_encoder(self, mock_app):
        handler = EncoderHandler(mock_app)
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TEMPO_ENCODER', 'tempo'):
            result = handler.handle_encoder_rotation('tempo', 5)
            
        assert result is True
        mock_app.sequencer.set_bpm.assert_called_with(125)
        
    def test_tempo_encoder_bounds(self, mock_app):
        handler = EncoderHandler(mock_app)
        mock_app.sequencer.bpm = 200
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TEMPO_ENCODER', 'tempo'):
            handler.handle_encoder_rotation('tempo', 5)
            
        # Should not exceed 200
        mock_app.sequencer.set_bpm.assert_not_called()
        
    def test_device_selection_encoder(self, mock_app):
        handler = EncoderHandler(mock_app)
        mock_app.device_selection_mode = True
        mock_app.encoder_threshold = 1  # Lower threshold for testing
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TRACK1_ENCODER', 'track1'):
            result = handler.handle_encoder_rotation('track1', 1)
            
        assert result is True
        assert mock_app.device_selection_index == 1
        
    def test_device_selection_encoder_wraps(self, mock_app):
        handler = EncoderHandler(mock_app)
        mock_app.device_selection_mode = True
        mock_app.encoder_threshold = 1
        mock_app.device_selection_index = 2  # Last device
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TRACK1_ENCODER', 'track1'):
            handler.handle_encoder_rotation('track1', 1)
            
        assert mock_app.device_selection_index == 0  # Should wrap to 0
        
    def test_channel_selection_encoder(self, mock_app):
        handler = EncoderHandler(mock_app)
        mock_app.device_selection_mode = True
        mock_device = Mock()
        mock_device.channel = 1
        mock_app.device_manager.get_device_by_index.return_value = mock_device
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TRACK2_ENCODER', 'track2'):
            result = handler.handle_encoder_rotation('track2', 3)
            
        assert result is True
        assert mock_device.channel == 4
        
    def test_channel_selection_bounds(self, mock_app):
        handler = EncoderHandler(mock_app)
        mock_app.device_selection_mode = True
        mock_device = Mock()
        mock_device.channel = 16
        mock_app.device_manager.get_device_by_index.return_value = mock_device
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TRACK2_ENCODER', 'track2'):
            handler.handle_encoder_rotation('track2', 5)
            
        assert mock_device.channel == 16  # Should not exceed 16
        
    def test_clock_selection_encoder(self, mock_app):
        handler = EncoderHandler(mock_app)
        mock_app.clock_selection_mode = True
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TRACK1_ENCODER', 'track1'):
            result = handler.handle_encoder_rotation('track1', 1)
            
        assert result is True
        assert mock_app.clock_selection_index == 1
        
    def test_cc_encoder(self, mock_app):
        handler = EncoderHandler(mock_app)
        mock_device = Mock()
        mock_device.channel = 1
        mock_device.port = 'test_port'
        mock_app.tracks[0] = mock_device
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TRACK1_ENCODER', 'track1'):
            with patch.dict('handlers.encoder_handler.push2_python.constants.__dict__', {
                'ENCODER_TRACK1_ENCODER': 'track1',
                'ENCODER_TRACK2_ENCODER': 'track2',
                'ENCODER_TRACK3_ENCODER': 'track3',
                'ENCODER_TRACK4_ENCODER': 'track4',
                'ENCODER_TRACK5_ENCODER': 'track5',
                'ENCODER_TRACK6_ENCODER': 'track6',
                'ENCODER_TRACK7_ENCODER': 'track7',
                'ENCODER_TRACK8_ENCODER': 'track8'
            }):
                result = handler.handle_encoder_rotation('track1', 10)
                
        assert result is True
        assert mock_app.cc_values['encoder_1']['value'] == 74
        mock_app.midi_output.send_cc.assert_called_with(1, 7, 74, 'test_port')
        
    def test_cc_encoder_bounds(self, mock_app):
        handler = EncoderHandler(mock_app)
        mock_device = Mock()
        mock_app.tracks[0] = mock_device
        mock_app.cc_values['encoder_1']['value'] = 127
        
        with patch('handlers.encoder_handler.push2_python.constants.ENCODER_TRACK1_ENCODER', 'track1'):
            with patch.dict('handlers.encoder_handler.push2_python.constants.__dict__', {
                'ENCODER_TRACK1_ENCODER': 'track1'
            }):
                handler.handle_encoder_rotation('track1', 10)
                
        assert mock_app.cc_values['encoder_1']['value'] == 127  # Should not exceed 127
        
    def test_unhandled_encoder(self, mock_app):
        handler = EncoderHandler(mock_app)
        
        result = handler.handle_encoder_rotation('unknown_encoder', 1)
        
        assert result is False