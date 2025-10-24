import pytest
from unittest.mock import Mock, patch
from handlers.transport_handler import TransportHandler

class TestTransportHandler:
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.sequencer = Mock()
        app.sequencer.is_playing = False
        app.sequencer.current_step = 5
        app.push = Mock()
        app.push.buttons = Mock()
        return app
        
    def test_handle_play_when_stopped(self, mock_app):
        handler = TransportHandler(mock_app)
        
        with patch('handlers.transport_handler.push2_python.constants.BUTTON_PLAY', 'play_btn'):
            with patch('handlers.transport_handler.push2_python.constants.ANIMATION_PULSING_QUARTER', 'pulse'):
                handler.handle_play()
                
        mock_app.sequencer.play.assert_called_once()
        mock_app.push.buttons.set_button_color.assert_called_with('play_btn', 'green', 'pulse')
        
    def test_handle_play_when_playing(self, mock_app):
        handler = TransportHandler(mock_app)
        mock_app.sequencer.is_playing = True
        
        with patch('handlers.transport_handler.push2_python.constants.BUTTON_PLAY', 'play_btn'):
            handler.handle_play()
            
        mock_app.sequencer.stop.assert_called_once()
        mock_app.push.buttons.set_button_color.assert_called_with('play_btn', 'white')
        
    def test_handle_stop(self, mock_app):
        handler = TransportHandler(mock_app)
        
        with patch('handlers.transport_handler.push2_python.constants.BUTTON_PLAY', 'play_btn'):
            handler.handle_stop()
            
        mock_app.sequencer.stop.assert_called_once()
        assert mock_app.sequencer.current_step == 0
        mock_app.push.buttons.set_button_color.assert_called_with('play_btn', 'white')