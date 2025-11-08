import pytest
from unittest.mock import Mock, patch
import time
from sequencer import Sequencer, Pattern, Note

class TestPattern:
    def test_add_note(self):
        pattern = Pattern()
        pattern.add_note(0, 60, 100)
        
        notes = pattern.get_notes_at_step(0)
        assert len(notes) == 1
        assert notes[0].note == 60
        assert notes[0].velocity == 100
        
    def test_add_note_replaces_existing(self):
        pattern = Pattern()
        pattern.add_note(0, 60, 100)
        pattern.add_note(0, 62, 110)
        
        notes = pattern.get_notes_at_step(0)
        assert len(notes) == 1
        assert notes[0].note == 62
        
    def test_clear_step(self):
        pattern = Pattern()
        pattern.add_note(0, 60, 100)
        pattern.clear_step(0)
        
        notes = pattern.get_notes_at_step(0)
        assert len(notes) == 0

class TestSequencer:
    def test_init(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output, bpm=120)
        
        assert sequencer.bpm == 120
        assert len(sequencer.tracks) == 8
        assert not sequencer.is_playing
        assert sequencer.current_step == 0
        
    def test_set_bpm(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output)
        sequencer.set_bpm(140)
        
        assert sequencer.bpm == 140
        
    def test_set_track_channel(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output)
        sequencer.set_track_channel(0, 5)
        
        assert sequencer.track_channels[0] == 5
        
    def test_set_track_channel_bounds(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output)
        sequencer.set_track_channel(0, 0)  # Below min
        assert sequencer.track_channels[0] == 1
        
        sequencer.set_track_channel(0, 17)  # Above max
        assert sequencer.track_channels[0] == 16
        
    def test_play_stop(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output)
        
        try:
            sequencer.play()
            assert sequencer.is_playing
            
            sequencer.stop()
            assert not sequencer.is_playing
        finally:
            # Ensure sequencer is stopped to prevent thread leaks
            if sequencer.is_playing:
                sequencer.stop()
        
    @patch('time.time')
    def test_trigger_step_advances(self, mock_time, mock_midi_output):
        mock_time.return_value = 1000.0
        sequencer = Sequencer(mock_midi_output)
        sequencer.current_step = 5
        sequencer.current_step_notes = set()  # Initialize required attribute
        
        sequencer._trigger_step()
        
        assert sequencer.current_step == 6
        
    def test_trigger_step_wraps_at_default_length(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output)
        # Set first track to step 31 (last step of 32-step pattern)
        sequencer.current_steps = [31] + [0] * 7
        sequencer.current_step_notes = set()  # Initialize required attribute
        
        sequencer._trigger_step()
        
        # Should wrap to 0 (default pattern length is now 32)
        assert sequencer.current_step == 0
        assert sequencer.current_steps[0] == 0
        
    @patch('time.time')
    def test_trigger_step_plays_notes(self, mock_time, mock_midi_output):
        mock_time.return_value = 1000.0
        sequencer = Sequencer(mock_midi_output)
        sequencer.current_step_notes = set()  # Initialize required attribute
        
        # Add note to track 0 at step 0
        sequencer.tracks[0].add_note(0, 60, 100)
        sequencer.current_step = 0
        
        sequencer._trigger_step()
        
        mock_midi_output.send_note_on.assert_called_once_with(1, 60, 100, None)
        
    def test_handle_midi_clock_increments_count(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output)
        initial_count = sequencer._clock_count
        
        sequencer.handle_midi_clock()
        
        assert sequencer._clock_count == initial_count + 1
        
    def test_handle_midi_start_enables_external_sync(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output)
        
        with patch.object(sequencer, 'play') as mock_play:
            sequencer.handle_midi_start()
            
        assert sequencer.external_sync
        assert sequencer.current_step == 0
        mock_play.assert_called_once()
        
    def test_handle_midi_stop_disables_external_sync(self, mock_midi_output):
        sequencer = Sequencer(mock_midi_output)
        sequencer.external_sync = True
        
        with patch.object(sequencer, 'stop') as mock_stop:
            sequencer.handle_midi_stop()
            
        assert not sequencer.external_sync
        mock_stop.assert_called_once()
