import pytest
from unittest.mock import Mock, patch
from handlers.clock_handler import ClockHandler

class TestClockHandler:
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.clock_selection_mode = False
        app.clock_selection_index = 0
        app.midi_output = Mock()
        app.midi_output.clock_sources = ['Internal', 'Clock1', 'Clock2']
        return app
        
    def test_handle_metronome_button_enable(self, mock_app):
        handler = ClockHandler(mock_app)
        
        with patch('handlers.clock_handler.time.time', return_value=1000.0):
            handler.handle_metronome_button()
            
        assert mock_app.clock_selection_mode is True
        assert mock_app.last_encoder_time == 1000.0
        
    def test_handle_metronome_button_disable(self, mock_app):
        handler = ClockHandler(mock_app)
        mock_app.clock_selection_mode = True
        
        handler.handle_metronome_button()
        
        assert mock_app.clock_selection_mode is False
        
    def test_handle_confirm_clock_selection_valid(self, mock_app):
        handler = ClockHandler(mock_app)
        mock_app.clock_selection_mode = True
        mock_app.clock_selection_index = 1
        
        handler.handle_confirm_clock_selection()
        
        mock_app.midi_output.select_clock_source.assert_called_with('Clock1')
        assert mock_app.clock_selection_mode is False
        
    def test_handle_confirm_clock_selection_invalid_index(self, mock_app):
        handler = ClockHandler(mock_app)
        mock_app.clock_selection_mode = True
        mock_app.clock_selection_index = 5  # Out of range
        
        handler.handle_confirm_clock_selection()
        
        mock_app.midi_output.select_clock_source.assert_not_called()
        assert mock_app.clock_selection_mode is False
        
    def test_handle_confirm_clock_selection_no_sources(self, mock_app):
        handler = ClockHandler(mock_app)
        mock_app.clock_selection_mode = True
        mock_app.midi_output.clock_sources = []
        
        handler.handle_confirm_clock_selection()
        
        mock_app.midi_output.select_clock_source.assert_not_called()
        assert mock_app.clock_selection_mode is False
        
    def test_handle_confirm_clock_selection_not_in_mode(self, mock_app):
        handler = ClockHandler(mock_app)
        mock_app.clock_selection_mode = False
        
        handler.handle_confirm_clock_selection()
        
        mock_app.midi_output.select_clock_source.assert_not_called()