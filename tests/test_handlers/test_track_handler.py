import pytest
from unittest.mock import Mock
from handlers.track_handler import TrackHandler

class TestTrackHandler:
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.tracks = [Mock(), None, Mock(), None, None, None, None, None]  # Some tracks assigned
        app.current_track = 0
        app.held_track_button = None
        app.track_edit_mode = False
        app.track_muted = [False] * 8
        app.solo_mode = False
        app.soloed_track = None
        app.pad_states = {}
        app._update_track_buttons = Mock()
        app._init_cc_values_for_track = Mock()
        app._update_mute_solo_buttons = Mock()
        app._update_pad_colors = Mock()
        return app
        
    def test_handle_track_selection_valid_track(self, mock_app):
        handler = TrackHandler(mock_app)
        
        handler.handle_track_selection(2)
        
        assert mock_app.held_track_button == 2
        assert mock_app.current_track == 2
        mock_app._update_track_buttons.assert_called_once()
        mock_app._init_cc_values_for_track.assert_called_once()
        mock_app._update_mute_solo_buttons.assert_called_once()
        mock_app._update_pad_colors.assert_called_once()
        assert mock_app.pad_states == {}  # Should be cleared
        
    def test_handle_track_selection_empty_track(self, mock_app):
        handler = TrackHandler(mock_app)
        
        handler.handle_track_selection(1)  # Track 1 is None
        
        # Should not change anything for empty track
        assert mock_app.held_track_button is None
        assert mock_app.current_track == 0  # Unchanged
        mock_app._update_track_buttons.assert_not_called()
        
    def test_handle_track_selection_invalid_track(self, mock_app):
        handler = TrackHandler(mock_app)
        
        handler.handle_track_selection(8)  # Out of range
        
        assert mock_app.held_track_button is None
        mock_app._update_track_buttons.assert_not_called()
        
    def test_handle_track_release_normal_mode(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.held_track_button = 2
        
        handler.handle_track_release()
        
        assert mock_app.held_track_button is None
        
    def test_handle_track_release_edit_mode(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.held_track_button = 2
        mock_app.track_edit_mode = True
        
        handler.handle_track_release()
        
        assert mock_app.held_track_button == 2  # Should not clear in edit mode
        
    def test_handle_mute_toggle_on(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.current_track = 0
        
        handler.handle_mute()
        
        assert mock_app.track_muted[0] is True
        mock_app._update_mute_solo_buttons.assert_called_once()
        
    def test_handle_mute_toggle_off(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.current_track = 0
        mock_app.track_muted[0] = True
        
        handler.handle_mute()
        
        assert mock_app.track_muted[0] is False
        mock_app._update_mute_solo_buttons.assert_called_once()
        
    def test_handle_mute_empty_track(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.current_track = 1  # Empty track
        
        handler.handle_mute()
        
        # Should do nothing for empty track
        assert mock_app.track_muted[1] is False
        mock_app._update_mute_solo_buttons.assert_not_called()
        
    def test_handle_solo_enable(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.current_track = 0
        
        handler.handle_solo()
        
        assert mock_app.solo_mode is True
        assert mock_app.soloed_track == 0
        mock_app._update_mute_solo_buttons.assert_called_once()
        
    def test_handle_solo_disable(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.current_track = 0
        mock_app.solo_mode = True
        mock_app.soloed_track = 0
        
        handler.handle_solo()
        
        assert mock_app.solo_mode is False
        assert mock_app.soloed_track is None
        mock_app._update_mute_solo_buttons.assert_called_once()
        
    def test_handle_solo_switch_track(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.current_track = 2
        mock_app.solo_mode = True
        mock_app.soloed_track = 0  # Different track soloed
        
        handler.handle_solo()
        
        assert mock_app.solo_mode is True
        assert mock_app.soloed_track == 2  # Should switch to current track
        
    def test_handle_solo_empty_track(self, mock_app):
        handler = TrackHandler(mock_app)
        mock_app.current_track = 1  # Empty track
        
        handler.handle_solo()
        
        # Should do nothing for empty track
        assert mock_app.solo_mode is False
        mock_app._update_mute_solo_buttons.assert_not_called()