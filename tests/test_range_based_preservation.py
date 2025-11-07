import pytest
from unittest.mock import Mock
from sequencer import Sequencer, Pattern, Note

class TestRangeBasedNotePreservation:
    """Test range-based note preservation and restoration functionality"""
    
    def test_range_change_preserves_and_restores_notes(self):
        """Test that notes are preserved when changing ranges and restored when changing back"""
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # Step 1: Add notes at various positions
        sequencer.tracks[0].add_note(1, 60, 100)   # Position 1
        sequencer.tracks[0].add_note(9, 62, 100)   # Position 9  
        sequencer.tracks[0].add_note(17, 64, 100)  # Position 17
        sequencer.tracks[0].add_note(25, 66, 100)  # Position 25
        
        assert len(sequencer.tracks[0].notes) == 4
        note_positions = {note.step for note in sequencer.tracks[0].notes}
        assert note_positions == {1, 9, 17, 25}
        
        # Step 2: Change to range 10-24 (start 10, length 15)
        sequencer.set_pattern_length(0, 15, range_start=10)
        
        assert sequencer.get_pattern_length(0) == 15
        range_starts = getattr(sequencer, '_range_starts', {})
        assert range_starts[0] == 10
        
        # Should have 1 active note (position 17) and 3 preserved notes
        active_notes = sequencer.tracks[0].notes
        preserved_notes = getattr(sequencer, '_preserved_notes', {})[0]
        
        assert len(active_notes) == 1  # Only note 17
        assert len(preserved_notes) == 3  # Notes at 1, 9, 25
        assert active_notes[0].step == 7  # Position 17 becomes step 7 (17-10=7)
        
        # Step 3: Change back to full range 0-31 (start 0, length 32)
        sequencer.set_pattern_length(0, 32, range_start=0)
        
        assert sequencer.get_pattern_length(0) == 32
        range_starts = getattr(sequencer, '_range_starts', {})
        assert range_starts[0] == 0
        
        # All notes should be restored
        final_active_notes = sequencer.tracks[0].notes
        final_preserved_notes = getattr(sequencer, '_preserved_notes', {})[0]
        
        assert len(final_active_notes) == 4  # All 4 notes restored
        assert len(final_preserved_notes) == 0  # Nothing preserved
        
        final_note_positions = {note.step for note in final_active_notes}
        assert final_note_positions == {1, 9, 17, 25}  # All original positions

    def test_multiple_range_changes_preserve_all_notes(self):
        """Test that multiple range changes don't lose any notes"""
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # Add notes at various positions across the full range
        test_positions = [2, 5, 8, 12, 16, 20, 28, 30]
        for pos in test_positions:
            sequencer.tracks[0].add_note(pos, 60 + pos, 100)
        
        assert len(sequencer.tracks[0].notes) == 8
        
        # Change to range 10-22 (partial overlap)
        sequencer.set_pattern_length(0, 13, range_start=10)
        
        # Only notes within 10-22 should be active: 12, 16, 20
        active_notes = sequencer.tracks[0].notes
        assert len(active_notes) == 3
        
        # Change to range 25-30 (different range, no overlap)
        sequencer.set_pattern_length(0, 6, range_start=25)
        
        # Only note at 28, 30 should be active
        active_notes = sequencer.tracks[0].notes
        assert len(active_notes) == 2
        
        # Change back to full range
        sequencer.set_pattern_length(0, 32, range_start=0)
        
        # All original notes should be restored
        final_active_notes = sequencer.tracks[0].notes
        assert len(final_active_notes) == 8
        
        final_note_positions = {note.step for note in final_active_notes}
        assert final_note_positions == set(test_positions)

    def test_range_changes_preserve_absolute_positioning(self):
        """Test that range changes maintain correct absolute positioning"""
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # Add a distinctive note at position 15
        sequencer.tracks[0].add_note(15, 88, 100)  # High note at position 15
        
        # Change to range 10-20 (includes position 15)
        sequencer.set_pattern_length(0, 11, range_start=10)
        
        # Note should be at step 5 (15-10=5)
        active_notes = sequencer.tracks[0].notes
        assert len(active_notes) == 1
        assert active_notes[0].step == 5
        assert active_notes[0].note == 88  # Same note value
        
        # Change to range 5-15 (different range, still includes position 15)
        sequencer.set_pattern_length(0, 11, range_start=5)
        
        # Note should still be at step 10 (15-5=10)
        active_notes = sequencer.tracks[0].notes
        assert len(active_notes) == 1
        assert active_notes[0].step == 10
        assert active_notes[0].note == 88  # Same note value
        
        # Change back to full range
        sequencer.set_pattern_length(0, 32, range_start=0)
        
        # Note should be back at position 15
        final_active_notes = sequencer.tracks[0].notes
        assert len(final_active_notes) == 1
        assert final_active_notes[0].step == 15
        assert final_active_notes[0].note == 88

    def test_range_with_no_overlap_preserves_all_notes(self):
        """Test that ranges with no overlap preserve all notes"""
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # Add notes in the first half
        sequencer.tracks[0].add_note(2, 60, 100)
        sequencer.tracks[0].add_note(7, 62, 100)
        sequencer.tracks[0].add_note(12, 64, 100)
        
        # Change to range in the second half (no overlap)
        sequencer.set_pattern_length(0, 10, range_start=20)
        
        # No notes should be active (all preserved)
        active_notes = sequencer.tracks[0].notes
        assert len(active_notes) == 0
        
        preserved_notes = getattr(sequencer, '_preserved_notes', {})[0]
        assert len(preserved_notes) == 3  # All notes preserved
        
        # Change back to full range
        sequencer.set_pattern_length(0, 32, range_start=0)
        
        # All notes should be restored
        final_active_notes = sequencer.tracks[0].notes
        assert len(final_active_notes) == 3
        
        final_note_positions = {note.step for note in final_active_notes}
        assert final_note_positions == {2, 7, 12}
