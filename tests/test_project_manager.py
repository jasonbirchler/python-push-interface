import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from project_manager import ProjectManager

class TestProjectManager:
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.sequencer = Mock()
        app.sequencer.bpm = 120
        app.sequencer.tracks = [Mock() for _ in range(8)]
        app.current_track = 0
        app.tracks = [None] * 8
        app.device_manager = Mock()
        app.midi_output = Mock()
        app._update_track_buttons = Mock()
        app._init_cc_values_for_track = Mock()
        app._update_pad_colors = Mock()
        app.pad_states = {}
        
        # Mock pattern notes
        for i in range(8):
            app.sequencer.tracks[i].notes = []
            
        return app
        
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
            
    def test_init_creates_projects_dir(self, mock_app):
        with patch('project_manager.os.path.expanduser') as mock_expand:
            with patch('project_manager.os.makedirs') as mock_makedirs:
                with patch('project_manager.os.path.exists', return_value=False):
                    mock_expand.return_value = '/test/projects'
                    
                    pm = ProjectManager(mock_app)
                    
                    assert pm.projects_dir == '/test/projects'
                    mock_makedirs.assert_called_once_with('/test/projects')
                    
    def test_init_existing_projects_dir(self, mock_app):
        with patch('project_manager.os.path.expanduser', return_value='/test/projects'):
            with patch('project_manager.os.path.exists', return_value=True):
                with patch('project_manager.os.makedirs') as mock_makedirs:
                    
                    pm = ProjectManager(mock_app)
                    
                    mock_makedirs.assert_not_called()
                    
    def test_save_project_basic(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            with patch('project_manager.datetime') as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T12:00:00'
                
                pm.save_project('test_project')
                
        # Check file was created
        filepath = os.path.join(temp_dir, 'test_project.json')
        assert os.path.exists(filepath)
        
        # Check file content
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        assert data['version'] == '1.0'
        assert data['bpm'] == 120
        assert data['current_track'] == 0
        assert len(data['tracks']) == 8
        assert pm.current_project_file == 'test_project'
        
    def test_save_project_with_devices_and_notes(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            # Setup mock device
            mock_device = Mock()
            mock_app.tracks[0] = mock_device
            mock_app.device_manager.to_dict.return_value = {'name': 'Test Device'}
            
            # Setup mock notes
            mock_note = Mock()
            mock_note.step = 0
            mock_note.note = 60
            mock_note.velocity = 100
            mock_app.sequencer.tracks[0].notes = [mock_note]
            
            with patch('project_manager.datetime') as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T12:00:00'
                
                pm.save_project('test_with_data')
                
        # Check saved data
        filepath = os.path.join(temp_dir, 'test_with_data.json')
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        assert data['tracks'][0]['device'] == {'name': 'Test Device'}
        assert len(data['tracks'][0]['notes']) == 1
        assert data['tracks'][0]['notes'][0]['note'] == 60
        
    def test_load_project_file_not_found(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            result = pm.load_project('nonexistent')
            
            assert result is False
            
    def test_load_project_success(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            # Create test project file
            project_data = {
                'version': '1.0',
                'bpm': 140,
                'current_track': 2,
                'tracks': [
                    {
                        'index': 0,
                        'device': {'name': 'Test Device', 'port': 'Test Port', 'channel': 5},
                        'notes': [{'step': 0, 'note': 60, 'velocity': 100}]
                    }
                ] + [{'index': i, 'device': None, 'notes': []} for i in range(1, 8)]
            }
            
            filepath = os.path.join(temp_dir, 'test_load.json')
            with open(filepath, 'w') as f:
                json.dump(project_data, f)
                
            # Setup mocks
            mock_device = Mock()
            mock_app.device_manager.from_dict.return_value = mock_device
            mock_app.midi_output.connect.return_value = True
            
            result = pm.load_project('test_load')
            
            assert result is True
            assert pm.current_project_file == 'test_load'
            mock_app.sequencer.set_bpm.assert_called_with(140)
            assert mock_app.current_track == 2
            
    def test_load_project_device_connection_failed(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            # Create test project with device
            project_data = {
                'bpm': 120,
                'current_track': 0,
                'tracks': [
                    {
                        'index': 0,
                        'device': {'name': 'Test Device'},
                        'notes': []
                    }
                ] + [{'index': i, 'device': None, 'notes': []} for i in range(1, 8)]
            }
            
            filepath = os.path.join(temp_dir, 'test_fail.json')
            with open(filepath, 'w') as f:
                json.dump(project_data, f)
                
            # Setup mocks - connection fails
            mock_device = Mock()
            mock_app.device_manager.from_dict.return_value = mock_device
            mock_app.midi_output.connect.return_value = False
            
            result = pm.load_project('test_fail')
            
            assert result is True  # Load succeeds but device not assigned
            assert mock_app.tracks[0] is None  # Device not assigned due to connection failure
            
    def test_load_project_invalid_json(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            # Create invalid JSON file
            filepath = os.path.join(temp_dir, 'invalid.json')
            with open(filepath, 'w') as f:
                f.write('invalid json content')
                
            result = pm.load_project('invalid')
            
            assert result is False
            
    def test_clear_current_project(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            # Setup some state
            mock_app.tracks[0] = Mock()
            mock_app.current_track = 3
            pm.current_project_file = 'test'
            
            pm._clear_current_project()
            
            mock_app.sequencer.stop.assert_called_once()
            assert all(track is None for track in mock_app.tracks)
            assert mock_app.current_track == 0
            assert pm.current_project_file is None
            mock_app.sequencer.set_bpm.assert_called_with(120)
            
    def test_list_projects_empty_dir(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            projects = pm.list_projects()
            
            assert projects == []
            
    def test_list_projects_with_files(self, mock_app, temp_dir):
        with patch('project_manager.os.path.expanduser', return_value=temp_dir):
            pm = ProjectManager(mock_app)
            
            # Create test files
            open(os.path.join(temp_dir, 'project1.json'), 'w').close()
            open(os.path.join(temp_dir, 'project2.json'), 'w').close()
            open(os.path.join(temp_dir, 'not_project.txt'), 'w').close()  # Should be ignored
            
            projects = pm.list_projects()
            
            assert sorted(projects) == ['project1', 'project2']
            
    def test_list_projects_nonexistent_dir(self, mock_app):
        with patch('project_manager.os.path.expanduser', return_value='/nonexistent'):
            with patch('project_manager.os.makedirs'):
                with patch('project_manager.os.path.exists', return_value=False):
                    pm = ProjectManager(mock_app)
                    
                    projects = pm.list_projects()
                    
                    assert projects == []