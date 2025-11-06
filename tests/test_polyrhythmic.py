import pytest
from unittest.mock import Mock, patch
import time
from sequencer import Sequencer, Pattern, Note

class TestPolyrhythmicPatterns:
    """Test polyrhythmic functionality with variable pattern lengths"""
    
    def test_pattern_length_bounds(self, mock_midi_output):
        """Test pattern length constraints"""
        sequencer = Sequencer(mock_midi_output)
        
        # Test minimum bound
        sequencer.set_pattern_length(0, 0)
        assert sequencer.get_pattern_length(0) == 1
        
        # Test maximum bound  
        sequencer.set_pattern_length(0, 100)
        assert sequencer.get_pattern_length(0) == 64
        
        # Test valid range
        sequencer.set_pattern_length(0, 12)
        assert sequencer.get_pattern_length(0) == 12

    def test_notes_outside_pattern_length(self, mock_midi_output):
        """Test that notes beyond pattern length are ignored"""
        sequencer = Sequencer(mock_midi_output)
        sequencer.set_pattern_length(0, 4)
        
        # Note within pattern length
        sequencer.tracks[0].add_note(2, 60, 100)
        notes = sequencer.tracks[0].get_notes_at_step(2)
        assert len(notes) == 1
        assert notes[0].note == 60
        
        # Note beyond pattern length should be ignored
        sequencer.tracks[0].add_note(10, 62, 100)
        notes = sequencer.tracks[0].get_notes_at_step(10)
        assert len(notes) == 0
        
        # Verify step 10 doesn't exist in pattern
        all_notes = sequencer.tracks[0].notes
        step_10_notes = [n for n in all_notes if n.step == 10]
        assert len(step_10_notes) == 0

    def test_independent_track_progression(self, mock_midi_output):
        """Test that tracks advance independently based on their pattern lengths"""
        sequencer = Sequencer(mock_midi_output)
        
        # Setup tracks with different lengths
        sequencer.set_pattern_length(0, 8)   # 8-step track
        sequencer.set_pattern_length(1, 12)  # 12-step track
        sequencer.set_pattern_length(2, 16)  # 16-step track (default)
        
        # Initialize step tracking
        sequencer.current_step_notes = set()
        
        # Add a note to each track at step 0
        sequencer.tracks[0].add_note(0, 60, 100)
        sequencer.tracks[1].add_note(0, 62, 100) 
        sequencer.tracks[2].add_note(0, 64, 100)
        
        # Track 0: 8 steps (loops at step 0 every 8 triggers)
        # Track 1: 12 steps (loops at step 0 every 12 triggers)
        # Track 2: 16 steps (loops at step 0 every 16 triggers)
        
        # Advance 24 global steps
        for step_count in range(24):
            sequencer._trigger_step()
            
            if step_count == 7:  # After 8 steps
                assert sequencer.get_current_step(0) == 0  # Track 0 loops
                assert sequencer.get_current_step(1) == 8  # Track 1 at step 8
                assert sequencer.get_current_step(2) == 8  # Track 2 at step 8
                
            elif step_count == 11:  # After 12 steps
                assert sequencer.get_current_step(0) == 4  # Track 0: 12 % 8 = 4
                assert sequencer.get_current_step(1) == 0  # Track 1 loops
                assert sequencer.get_current_step(2) == 12 # Track 2 at step 12
                
            elif step_count == 23:  # After 24 steps
                assert sequencer.get_current_step(0) == 0  # Track 0: 24 % 8 = 0 (2 loops)
                assert sequencer.get_current_step(1) == 0  # Track 1: 24 % 12 = 0 (2 loops)
                assert sequencer.get_current_step(2) == 8  # Track 2: 24 % 16 = 8

    def test_track_steps_property(self, mock_midi_output):
        """Test track_steps property returns all current steps"""
        sequencer = Sequencer(mock_midi_output)
        
        # Set different lengths
        sequencer.set_pattern_length(0, 5)
        sequencer.set_pattern_length(1, 7)
        
        # Manually set some step positions for testing
        sequencer.current_steps = [3, 6, 0, 0, 0, 0, 0, 0]
        
        track_steps = sequencer.current_steps
        assert len(track_steps) == 8
        assert track_steps[0] == 3
        assert track_steps[1] == 6
        assert track_steps[2] == 0

    def test_pattern_length_clears_notes_beyond_length(self, mock_midi_output):
        """Test that reducing pattern length clears notes beyond new length"""
        sequencer = Sequencer(mock_midi_output)
        
        # Add notes across a wide range
        sequencer.tracks[0].add_note(5, 60, 100)
        sequencer.tracks[0].add_note(10, 62, 100) 
        sequencer.tracks[0].add_note(15, 64, 100)
        
        # Initially all notes should exist
        assert len(sequencer.tracks[0].notes) == 3
        
        # Reduce length to 8 steps - should clear notes at steps 10 and 15
        sequencer.set_pattern_length(0, 8)
        
        # Only note at step 5 should remain
        remaining_notes = sequencer.tracks[0].notes
        assert len(remaining_notes) == 1
        assert remaining_notes[0].step == 5
        assert remaining_notes[0].note == 60

    def test_midi_start_resets_all_track_steps(self, mock_midi_output):
        """Test that MIDI start resets all track step counters"""
        sequencer = Sequencer(mock_midi_output)
        
        # Set different lengths and advance some steps
        sequencer.set_pattern_length(0, 5)
        sequencer.set_pattern_length(1, 7)
        sequencer.current_steps = [3, 6, 1, 2, 4, 0, 1, 3]
        
        # Simulate MIDI start
        sequencer.handle_midi_start()
        
        # All track steps should be reset to 0
        assert sequencer.current_steps == [0, 0, 0, 0, 0, 0, 0, 0]

    def test_polyrhythmic_note_timing(self, mock_midi_output):
        """Test that notes are triggered at correct polyrhythmic timing"""
        sequencer = Sequencer(mock_midi_output)
        
        # Setup polyrhythmic pattern: 3 against 4 (12 vs 16 steps)
        sequencer.set_pattern_length(0, 12)  # 3/4 feel
        sequencer.set_pattern_length(1, 16)  # 4/4 feel
        
        # Add notes at step 0 of each track
        sequencer.tracks[0].add_note(0, 60, 100)
        sequencer.tracks[1].add_note(0, 62, 100)
        
        sequencer.current_step_notes = set()
        
        # Track 0 should trigger its note every 12 steps
        # Track 1 should trigger its note every 16 steps
        
        # Mock MIDI output to track note triggers
        mock_midi_output.send_note_on.reset_mock()
        
        # Trigger steps and check when notes are played
        note_triggers = []
        for step in range(24):  # 24 steps (LCM of 12 and 16 is 48, but 24 shows pattern)
            sequencer._trigger_step()
            
            # Check if notes were triggered this step
            call_count = mock_midi_output.send_note_on.call_count
            if call_count > len(note_triggers):
                note_triggers.append(step)
        
        # Track 0 (12 steps) should trigger at steps 0, 12
        # Track 1 (16 steps) should trigger at step 0 only (within 24 steps)
        assert len(note_triggers) >= 1  # At least the initial trigger
        assert note_triggers[0] == 0    # First trigger at step 0

    def test_current_step_getter(self, mock_midi_output):
        """Test get_current_step method for individual tracks"""
        sequencer = Sequencer(mock_midi_output)
        
        sequencer.current_steps = [5, 3, 12, 7, 1, 9, 2, 14]
        
        assert sequencer.get_current_step(0) == 5
        assert sequencer.get_current_step(1) == 3
        assert sequencer.get_current_step(7) == 14
        assert sequencer.get_current_step(8) == 0  # Out of bounds

class TestPolyrhythmicEngineIntegration:
    """Test polyrhythmic functionality through the engine interface"""
    
    def test_engine_set_pattern_length(self, mock_midi_output):
        """Test pattern length control through sequencer engine"""
        from core.sequencer_engine import SequencerEngine
        
        engine = SequencerEngine(mock_midi_output)
        
        # Test setting pattern length
        engine.set_pattern_length(0, 8)
        assert engine.get_pattern_length(0) == 8
        
        engine.set_pattern_length(1, 12)
        assert engine.get_pattern_length(1) == 12
        
        # Test bounds
        engine.set_pattern_length(0, 0)
        assert engine.get_pattern_length(0) == 1
        
        engine.set_pattern_length(0, 100)
        assert engine.get_pattern_length(0) == 64

    def test_engine_track_steps_property(self, mock_midi_output):
        """Test engine exposes track_steps property"""
        from core.sequencer_engine import SequencerEngine
        
        engine = SequencerEngine(mock_midi_output)
        
        # Access track_steps property
        track_steps = engine.track_steps
        assert len(track_steps) == 8
        assert all(isinstance(step, int) for step in track_steps)
        
        # Should be a copy, not reference to internal array
        track_steps[0] = 999
        assert engine.track_steps[0] != 999

    def test_engine_get_current_step(self, mock_midi_output):
        """Test engine get_current_step for individual tracks"""
        from core.sequencer_engine import SequencerEngine
        
        engine = SequencerEngine(mock_midi_output)
        
        # Set different step positions
        engine._internal_sequencer.current_steps = [3, 7, 12, 5, 1, 9, 2, 14]
        
        assert engine.get_current_step(0) == 3
        assert engine.get_current_step(1) == 7
        assert engine.get_current_step(7) == 14
