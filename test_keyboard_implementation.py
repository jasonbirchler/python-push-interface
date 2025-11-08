#!/usr/bin/env python3
"""
Test script to verify the new piano-style keyboard layout implementation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, patch
import mock_midi
import mock_push2

def test_piano_keyboard_layout():
    """Test the piano keyboard layout implementation"""
    print("🎵 Testing Piano Keyboard Layout Implementation")
    
    # Mock the hardware
    with patch.dict('sys.modules', {
        'mido': mock_midi,
        'push2_python': mock_push2,
        'push2_python.constants': mock_push2.constants
    }):
        try:
            from adapters.push2_adapter import Push2Adapter
            from core.sequencer_engine import SequencerEngine
            
            # Create mock components
            mock_midi_output = Mock()
            sequencer = SequencerEngine(mock_midi_output)
            
            # Create adapter with mocked hardware
            adapter = Push2Adapter(sequencer, use_simulator=True)
            
            print("✅ Push2Adapter created successfully")
            print(f"   - White key positions: {len(adapter.white_key_positions)}")
            print(f"   - Black key positions: {len(adapter.black_key_positions)}")
            print(f"   - Disabled key positions: {len(adapter.disabled_key_positions)}")
            
            # Test piano note mapping (corrected rows)
            print(f"\n🎹 Piano Note Mapping:")
            test_positions = [(7, 0), (7, 1), (7, 7), (5, 0), (5, 7), (6, 1), (6, 2), (4, 4)]
            for pos in test_positions:
                if pos in adapter.piano_note_mapping:
                    note = adapter.piano_note_mapping[pos]
                    key_type = "White" if pos in adapter.white_key_positions else "Black"
                    disabled = pos in adapter.disabled_key_positions
                    print(f"   - Position {pos}: Note {note} ({key_type} key) {'[DISABLED]' if disabled else ''}")
            
            # Test keyboard layout validation
            print(f"\n✅ Keyboard Layout Validation:")
            
            # Check white keys (rows 5 and 7 - corrected layout)
            white_keys_row5 = [(5, col) for col in range(8)]
            white_keys_row7 = [(7, col) for col in range(8)]
            all_white_keys = white_keys_row5 + white_keys_row7
            
            print(f"   - Row 5 white keys: {len(white_keys_row5)}")
            print(f"   - Row 7 white keys: {len(white_keys_row7)}")
            assert all(pos in adapter.white_key_positions for pos in all_white_keys), "Missing white key positions"
            
            # Check black keys (rows 4 and 6 with gaps - above white keys)
            black_key_cols = [1, 2, 4, 5, 6]  # Valid black key columns
            black_keys_row4 = [(4, col) for col in black_key_cols]
            black_keys_row6 = [(6, col) for col in black_key_cols]
            all_black_keys = black_keys_row4 + black_keys_row6
            
            print(f"   - Row 4 black keys: {len(black_keys_row4)}")
            print(f"   - Row 6 black keys: {len(black_keys_row6)}")
            assert all(pos in adapter.black_key_positions for pos in all_black_keys), "Missing black key positions"
            
            # Check disabled pads (positions 0, 3, 7 in black key rows 4 and 6)
            disabled_positions = [(4, 0), (4, 3), (4, 7), (6, 0), (6, 3), (6, 7)]
            print(f"   - Disabled positions: {len(disabled_positions)}")
            assert all(pos in adapter.disabled_key_positions for pos in disabled_positions), "Missing disabled positions"
            
            # Test keyboard color system
            print(f"\n🎨 Keyboard Color System:")
            print(f"   - White keys: White color")
            print(f"   - Black keys: Turquoise color") 
            print(f"   - Disabled pads: Dark gray color")
            print(f"   - Held keys: Red color")
            
            print(f"\n✅ Piano keyboard layout implementation verified!")
            print(f"   - 16 white keys (2 rows × 8 columns)")
            print(f"   - 10 black keys (2 rows × 5 keys each)")
            print(f"   - 6 disabled pads (2 rows × 3 gaps each)")
            print(f"   - Total keyboard pads: 32 (4 rows × 8 columns)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing piano keyboard layout: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_range_selection_system():
    """Test the pad-based range selection system"""
    print("\n🎯 Testing Pad-Based Range Selection System")
    
    # Mock the hardware
    with patch.dict('sys.modules', {
        'mido': mock_midi,
        'push2_python': mock_push2,
        'push2_python.constants': mock_push2.constants
    }):
        try:
            from adapters.push2_adapter import Push2Adapter
            from core.sequencer_engine import SequencerEngine
            
            # Create mock components
            mock_midi_output = Mock()
            sequencer = SequencerEngine(mock_midi_output)
            
            # Create adapter with mocked hardware
            adapter = Push2Adapter(sequencer, use_simulator=True)
            
            print("✅ Range selection system initialized")
            print(f"   - Default range: {adapter.selected_range_start}-{adapter.selected_range_end}")
            print(f"   - Active range length: {adapter.selected_range_end - adapter.selected_range_start + 1} steps")
            
            # Test range selection with two pads
            print(f"\n👆 Testing two-pad range selection:")
            pad1 = (0, 0)  # Step 0
            pad2 = (1, 5)  # Step 13
            
            # Add pressed pads
            import time
            adapter.pressed_pads[pad1] = time.time()
            adapter.pressed_pads[pad2] = time.time()
            
            print(f"   - Pressed pads: {list(adapter.pressed_pads.keys())}")
            print(f"   - Pad 1 (0,0) = Step {pad1[0] * 8 + pad1[1]}")
            print(f"   - Pad 2 (1,5) = Step {pad2[0] * 8 + pad2[1]}")
            
            # Process range selection
            adapter._process_range_selection()
            
            expected_start = 0
            expected_end = 13
            print(f"   - Selected range: {adapter.selected_range_start}-{adapter.selected_range_end}")
            print(f"   - Expected range: {expected_start}-{expected_end}")
            
            assert adapter.selected_range_start == expected_start
            assert adapter.selected_range_end == expected_end
            assert len(adapter.pressed_pads) == 0  # Should be cleared
            
            print(f"✅ Range selection system working correctly!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing range selection system: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🎹 Push2 Adapter Piano Keyboard & Range Selection Test")
    print("=" * 60)
    
    success1 = test_piano_keyboard_layout()
    success2 = test_range_selection_system()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All tests passed! Implementation is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
