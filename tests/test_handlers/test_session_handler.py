import pytest
from unittest.mock import Mock, patch
from handlers.session_handler import SessionHandler

class TestSessionHandler:
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.session_mode = False
        app.session_action = None
        return app
        
    def test_handle_session_button_enable(self, mock_app):
        handler = SessionHandler(mock_app)
        
        with patch('handlers.session_handler.time.time', return_value=1000.0):
            handler.handle_session_button()
            
        assert mock_app.session_mode is True
        assert mock_app.last_encoder_time == 1000.0
        
    def test_handle_session_button_disable(self, mock_app):
        handler = SessionHandler(mock_app)
        mock_app.session_mode = True
        mock_app.session_action = 'save'
        
        handler.handle_session_button()
        
        assert mock_app.session_mode is False
        assert mock_app.session_action is None
        
    def test_handle_open_project(self, mock_app):
        handler = SessionHandler(mock_app)
        mock_app.session_mode = True
        
        handler.handle_open_project()
        
        assert mock_app.session_action == 'open'
        assert mock_app.session_project_index == 0
        
    def test_handle_open_project_not_in_session_mode(self, mock_app):
        handler = SessionHandler(mock_app)
        mock_app.session_mode = False
        
        handler.handle_open_project()
        
        assert mock_app.session_action is None
        
    def test_handle_save_project(self, mock_app):
        handler = SessionHandler(mock_app)
        mock_app.session_mode = True
        
        handler.handle_save_project()
        
        assert mock_app.session_action == 'save'
        
    def test_handle_save_new_project(self, mock_app):
        handler = SessionHandler(mock_app)
        mock_app.session_mode = True
        
        handler.handle_save_new_project()
        
        assert mock_app.session_action == 'save_new'
        
    def test_handle_confirm_session_action(self, mock_app):
        handler = SessionHandler(mock_app)
        mock_app.session_mode = True
        mock_app.session_action = 'save'
        mock_app._execute_session_action = Mock()
        
        handler.handle_confirm_session_action()
        
        mock_app._execute_session_action.assert_called_once()
        
    def test_handle_confirm_session_action_no_action(self, mock_app):
        handler = SessionHandler(mock_app)
        mock_app.session_mode = True
        mock_app.session_action = None
        mock_app._execute_session_action = Mock()
        
        handler.handle_confirm_session_action()
        
        mock_app._execute_session_action.assert_not_called()
        
    def test_handle_confirm_session_action_not_in_session_mode(self, mock_app):
        handler = SessionHandler(mock_app)
        mock_app.session_mode = False
        mock_app.session_action = 'save'
        mock_app._execute_session_action = Mock()
        
        handler.handle_confirm_session_action()
        
        mock_app._execute_session_action.assert_not_called()