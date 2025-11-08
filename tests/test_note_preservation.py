import pytest
from unittest.mock import Mock
from sequencer import Sequencer, Pattern, Note

class TestNotePreservationBug:
    """Test that notes are preserved when pattern length changes"""
    
    def test_notes_preserved_when_shortening_and_extending(self):
        """Test the specific bug: notes beyond shortened range should be restored when extended"""
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # Track 0 starts with 32 steps (default)
        assert sequencer.get_pattern_length(0) == 32
        
        # Step 1: Add notes at steps 1, 9, 17, 25
        sequencer.tracks[0].add_note(1, 60, 100)   # Within first 16 steps
        sequencer.tracks[0].add_note(9, 62, 100)   # Within first 16 steps  
        sequencer.tracks[0].add_note(17, 64, 100)  # Beyond first 16 steps
        sequencer.tracks[0].add_note(25, 66, 100)  # Beyond first 16 steps
        
        # Verify all notes are present
        notes_step_1 = sequencer.tracks[0].get_notes_at_step(1)
        notes_step_9 = sequencer.tracks[0].get_notes_at_step( 9)
        notes_step_17 = sequencer.tracks[0].get_notes_at_step( 17)
        notes_step_25 = sequencer.tracks[0].get_notes_at_step( 25)
        
        assert len(notes_step_1) == 1
        assert len(notes_step_9) == 1
        assert len(notes_step_17) == 1
        assert len(notes_step_25) == 1
        
        print("✓ All notes added successfully")
        
        # Step 2: Shorten pattern to 16 steps
        sequencer.set_pattern_length(0, 16)
        
        # Notes at steps 1 and 9 should still be present (within range)
        notes_step_1_after = sequencer.tracks[0].get_notes_at_step(1)
        notes_step_9_after = sequencer.tracks[0].get_notes_at_step( 9)
        assert len(notes_step_1_after) == 1
        assert len(notes_step_9_after) == 1
        assert notes_step_1_after[0].note == 60
        assert notes_step_9_after[0].note == 62
        
        # Notes at steps 17 and 25 should be preserved (not in active pattern)
        notes_step_17_after = sequencer.tracks[0].get_notes_at_step( 17)
        notes_step_25_after = sequencer.tracks[0].get_notes_at_step( 25)
        assert len(notes_step_17_after) == 0  # Not in active pattern
        assert len(notes_step_25_after) == 0  # Not in active pattern
        
        print("✓ Pattern shortened to 16 steps, notes 17 and 25 preserved")
        
        # Step 3: Extend pattern back to 32 steps
        sequencer.set_pattern_length(0, 32)
        
        # All notes should be present again
        notes_step_1_restored = sequencer.tracks[0].get_notes_at_step(1)
        notes_step_9_restored = sequencer.tracks[0].get_notes_at_step( 9)
        notes_step_17_restored = sequencer.tracks[0].get_notes_at_step( 17)
        notes_step_25_restored = sequencer.tracks[0].get_notes_at_step( 25)
        
        assert len(notes_step_1_restored) == 1
        assert len(notes_step_9_restored) == 1
        assert len(notes_step_17_restored) == 1  # CRITICAL: This was the bug
        assert len(notes_step_25_restored) == 1  # CRITICAL: This was the bug
        
        # Verify note values are preserved
        assert notes_step_17_restored[0].note == 64
        assert notes_step_25_restored[0].note == 66
        
        print("✓ Pattern extended back to 32 steps, all notes restored!")
    
    def test_multiple_shorten_extend_cycles(self):
        """Test that note preservation works through multiple cycles"""
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # Add notes at various positions
        test_notes = [(2, 60), (8, 62), (15, 64), (20, 66), (28, 68), (31, 70)]
        for step, note_value in test_notes:
            sequencer.tracks[0].add_note(step, note_value, 100)
        
        # Cycle 1: 32 -> 16 -> 32
        sequencer.set_pattern_length(0, 16)
        sequencer.set_pattern_length(0, 32)
        
        # Verify all notes are still there
        for step, expected_note in test_notes:
            notes = sequencer.tracks[0].get_notes_at_step( step)
            assert len(notes) == 1
            assert notes[0].note == expected_note
        
        # Cycle 2: 32 -> 8 -> 32
        sequencer.set_pattern_length(0, 8)
        sequencer.set_pattern_length(0, 32)
        
        # Verify all notes are still there
        for step, expected_note in test_notes:
            notes = sequencer.tracks[0].get_notes_at_step( step)
            assert len(notes) == 1
            assert notes[0].note == expected_note
        
        # Cycle 3: 32 -> 24 -> 32
        sequencer.set_pattern_length(0, 24)
        sequencer.set_pattern_length(0, 32)
        
        # Verify all notes are still there
        for step, expected_note in test_notes:
            notes = sequencer.tracks[0].get_notes_at_step( step)
            assert len(notes) == 1
            assert notes[0].note == expected_note
        
        print("✓ Multiple shorten/extend cycles preserved all notes")
    
    def test_preserved_notes_dont_conflict_with_new_notes(self):
        """Test that preserved notes don't conflict with newly added notes"""
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # Add initial note at step 20
        sequencer.tracks[0].add_note(20, 60, 100)
        assert len(sequencer.tracks[0].get_notes_at_step( 20)) == 1
        
        # Shorten to 16 steps
        sequencer.set_pattern_length(0, 16)
        
        # Extend back to 24 steps and add new note at step 20
        sequencer.set_pattern_length(0, 24)
        sequencer.tracks[0].add_note(20, 62, 100)  # Should replace the preserved note
        
        # Should have only one note at step 20, and it should be the new one
        notes = sequencer.tracks[0].get_notes_at_step( 20)
        assert len(notes) == 1
        assert notes[0].note == 62  # New note, not preserved note
        
        print("✓ New notes properly replace preserved notes")
    
    def test_partial_preservation(self):
        """Test that only notes within new extended range are restored"""
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # Add notes at steps 5, 10, 15, 20, 25, 30
        test_notes = [(5, 60), (10, 62), (15, 64), (20, 66), (25, 68), (30, 70)]
        for step, note_value in test_notes:
            sequencer.tracks[0].add_note(step, note_value, 100)
        
        # Shorten to 18 steps
        sequencer.set_pattern_length(0, 18)
        
        # Extend to 22 steps - should only restore notes within 0-21 range
        sequencer.set_pattern_length(0, 22)
        
        # Check which notes are restored
        restored_notes = []
        for step in [5, 10, 15, 20]:  # Should be restored
            notes = sequencer.tracks[0].get_notes_at_step( step)
            if notes:
                restored_notes.append(step)
        
        not_restored_notes = []
        for step in [25, 30]:  # Should still be preserved but not active
            notes = sequencer.tracks[0].get_notes_at_step( step)
            if not notes:
                not_restored_notes.append(step)
        
        assert len(restored_notes) == 4
        assert len(not_restored_notes) == 2
        
        print("✓ Partial preservation works correctly")
