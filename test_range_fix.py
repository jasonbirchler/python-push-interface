#!/usr/bin/env python3
"""
Test the range-based selection bug fix
"""

from unittest.mock import Mock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sequencer import Sequencer, Pattern, Note

def test_range_selection_respects_absolute_positions():
    """Test that when range changes, notes play at correct absolute positions"""
    print("Testing range-based selection bug fix...")
    
    mock_midi_output = Mock()
    sequencer = Sequencer(mock_midi_output)
    
    # Step 1: Start with 32 steps and add notes at positions 1, 9, 17, 25
    assert sequencer.get_pattern_length(0) == 32
    
    sequencer.tracks[0].add_note(1, 60, 100)   # Position 1
    sequencer.tracks[0].add_note(9, 62, 100)   # Position 9  
    sequencer.tracks[0].add_note(17, 64, 100)  # Position 17
    sequencer.tracks[0].add_note(25, 66, 100)  # Position 25
    
    # Verify all notes are present at their absolute positions
    assert len(sequencer.tracks[0].get_notes_at_step(1)) == 1
    assert len(sequencer.tracks[0].get_notes_at_step(9)) == 1
    assert len(sequencer.tracks[0].get_notes_at_step(17)) == 1
    assert len(sequencer.tracks[0].get_notes_at_step(25)) == 1
    
    print("✓ Step 1: All notes added at correct absolute positions")
    
    # Step 2: Change range to steps 10-24 (length 15, start 10)
    sequencer.set_pattern_length(0, 15, range_start=10)
    
    # Verify range change worked
    assert sequencer.get_pattern_length(0) == 15
    range_starts = getattr(sequencer, '_range_starts', {})
    assert range_starts[0] == 10
    
    # Step 3: Check which notes should be active in the new range (10-24)
    # Notes at 17 should be preserved (within range 10-24)
    # Notes at 1, 9, 25 should be preserved but not active (outside range)
    
    # Check that we have the right pattern structure
    assert len(sequencer.tracks[0].notes) == 1  # Only note 17 should be active
    active_note = sequencer.tracks[0].notes[0]
    assert active_note.step == 7  # Note 17 becomes step 7 in 15-step pattern (17-10=7)
    assert active_note.note == 64  # Should be the note from position 17
    
    # Verify preserved notes storage contains the excluded notes
    preserved_notes = getattr(sequencer, '_preserved_notes', {})[0]
    assert 1 in preserved_notes  # Note at position 1 preserved
    assert 9 in preserved_notes  # Note at position 9 preserved
    assert 25 in preserved_notes  # Note at position 25 preserved
    assert 17 not in preserved_notes  # Note at position 17 is active, not preserved
    
    print("✓ Step 2: Range changed to 10-24, only note 17 is active (as step 7)")
    print("✓ Step 3: Notes at 1, 9, 25 preserved but inactive")
    
    # Step 4: Simulate playback and verify only note 17 plays
    sequencer.current_step_notes = set()
    
    # Test several steps in the pattern
    test_steps = [0, 1, 2, 6, 7, 8, 14]  # Various steps in 15-step pattern
    
    for step in test_steps:
        sequencer.current_steps[0] = step
        sequencer._trigger_step()
        
        # Only step 7 (which corresponds to absolute position 17) should trigger a note
        if step == 7:
            # Should trigger note 64 (from absolute position 17)
            mock_midi_output.send_note_on.assert_called_with(1, 64, 100, None)
            print(f"✓ Step {step} correctly triggered note 64 (from absolute position 17)")
        else:
            # Should not trigger any note
            assert mock_midi_output.send_note_on.call_count == 0
            print(f"✓ Step {step} correctly triggered no note")
        
        # Clear for next test
        mock_midi_output.reset_mock()
    
    print("✓ Step 4: Playback test - only step 7 (position 17) triggers note")
    
    # Step 5: Test that extending range restores other notes
    sequencer.set_pattern_length(0, 32, range_start=0)  # Back to full range
    
    # All original notes should be restored
    assert len(sequencer.tracks[0].notes) == 4  # All 4 notes should be active again
    note_positions = {note.step for note in sequencer.tracks[0].notes}
    assert note_positions == {1, 9, 17, 25}  # All original positions restored
    
    print("✓ Step 5: Full range restored, all 4 notes active again")
    print("✅ RANGE-BASED SELECTION BUG IS FIXED!")

if __name__ == "__main__":
    test_range_selection_respects_absolute_positions()
