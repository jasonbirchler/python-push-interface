import pytest
from unittest.mock import Mock, patch
import time
from adapters.push2_adapter import Push2Adapter
from core.sequencer_engine import SequencerEngine

class TestUI_SequencerSynchronization:
    """Test that UI range selection properly synchronizes with sequencer pattern length"""
    
    @pytest.fixture
    def setup_ui_sync(self):
        """Set up UI-sequer synchronization test"""
        mock_midi_output = Mock()
        sequencer = SequencerEngine(mock_midi_output)
        
        # Create adapter with minimal initialization
        adapter = Push2Adapter.__new__(Push2Adapter)
        adapter.sequencer = sequencer
        adapter.selected_range_start = 0
        adapter.selected_range_end = 31
        adapter.keyboard_octave_offset = 0
        adapter.current_track = 0
        adapter.held_step_pad = None
        adapter.pressed_pads = {}
        adapter.held_keyboard_pads = set()
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.track_colors = ['red', 'blue', 'yellow', 'purple', 'cyan', 'pink', 'orange', 'lime']
        adapter.disabled_key_positions = set()
        adapter.white_key_positions = set()
        adapter.black_key_positions = set()
        adapter.keyboard_notes_c = set()
        
        # Mock Push2 hardware
        adapter.push = Mock()
        adapter.push.pads = Mock()
        
        adapter._setup_range_aware_note_system()
        
        return adapter, sequencer
    
    def test_range_selection_updates_sequencer_length(self, setup_ui_sync):
        """Test that 2-pad range selection updates sequencer pattern length"""
        adapter, sequencer = setup_ui_sync
        
        # Initialize missing attributes
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.current_track = 0
        
        # Initial state - should be 32 steps (default)
        assert sequencer.get_pattern_length(0) == 32
        
        # Simulate 2-pad press selecting range 0-15 (16 steps)
        pad1 = (0, 0)  # Step 0
        pad2 = (1, 7)  # Step 15
        adapter.pressed_pads[pad1] = time.time()
        adapter.pressed_pads[pad2] = time.time()
        
        # Process range selection
        adapter._process_range_selection()
        
        # Check that both UI and sequencer are synchronized
        assert adapter.selected_range_start == 0
        assert adapter.selected_range_end == 15
        assert adapter.selected_range_end - adapter.selected_range_start + 1 == 16
        assert sequencer.get_pattern_length(0) == 16  # CRITICAL: Sequencer should match UI
    
    def test_different_range_lengths_update_sequencer(self, setup_ui_sync):
        """Test various range lengths properly update sequencer"""
        adapter, sequencer = setup_ui_sync
        
        # Initialize missing attributes
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.current_track = 0
        
        test_cases = [
            ((0, 0), (0, 7), 8),   # 8 steps
            ((0, 0), (1, 3), 12),  # 12 steps  
            ((0, 0), (2, 5), 22),  # 22 steps
            ((0, 3), (3, 2), 24),  # 24 steps (3*8+2 - 0*8+3 + 1 = 26-3+1 = 24)
        ]
        
        for (pad1, pad2, expected_length) in test_cases:
            # Set up range selection
            adapter.pressed_pads[pad1] = time.time()
            adapter.pressed_pads[pad2] = time.time()
            
            # Process selection
            adapter._process_range_selection()
            
            # Verify both UI and sequencer are synchronized
            actual_length = adapter.selected_range_end - adapter.selected_range_start + 1
            assert actual_length == expected_length
            assert sequencer.get_pattern_length(0) == expected_length
            
            # Clear for next test
            adapter.selected_range_start = 0
            adapter.selected_range_end = 31
            adapter.pressed_pads.clear()
    
    def test_all_32_pads_lit_with_proper_dimming(self, setup_ui_sync):
        """Test that all 32 pads are lit with correct dimming"""
        adapter, sequencer = setup_ui_sync
        
        # Mock the Push2 hardware
        adapter.push = Mock()
        adapter.push.pads = Mock()
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.track_colors = ['red', 'blue', 'yellow', 'purple', 'cyan', 'pink', 'orange', 'lime']
        adapter.held_step_pad = None
        
        # Set a partial range (steps 5-20)
        adapter.selected_range_start = 5
        adapter.selected_range_end = 20
        
        # Call pad update
        adapter._update_pad_colors()
        
        # Verify all 64 pads were set to some color (32 sequencer + 32 keyboard)
        assert adapter.push.pads.set_pad_color.call_count == 64
        
        # Check pad color calls
        call_args_list = adapter.push.pads.set_pad_color.call_args_list
        
        # Check steps 0-4 (outside range) - should be light_gray
        for step in range(5):
            row, col = step // 8, step % 8
            pad_call = next((call for call in call_args_list if call[0][0] == (row, col)), None)
            assert pad_call is not None
            assert pad_call[0][1] == 'light_gray'
        
        # Check steps 5-20 (inside range) - should NOT be light_gray
        for step in range(5, 21):
            row, col = step // 8, step % 8
            pad_call = next((call for call in call_args_list if call[0][0] == (row, col)), None)
            assert pad_call is not None
            assert pad_call[0][1] != 'light_gray'  # Should be white, not light_gray
        
        # Check steps 21-31 (outside range) - should be light_gray
        for step in range(21, 32):
            row, col = step // 8, step % 8
            pad_call = next((call for call in call_args_list if call[0][0] == (row, col)), None)
            assert pad_call is not None
            assert pad_call[0][1] == 'light_gray'
    
    def test_keyboard_c_notes_highlighting(self, setup_ui_sync):
        """Test that C notes on keyboard are highlighted differently"""
        adapter, sequencer = setup_ui_sync
        
        # Mock the Push2 hardware
        adapter.push = Mock()
        adapter.push.pads = Mock()
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.track_colors = ['red', 'blue', 'yellow', 'purple', 'cyan', 'pink', 'orange', 'lime']
        adapter.disabled_key_positions = set()
        adapter.white_key_positions = set()
        adapter.black_key_positions = set()
        adapter.held_keyboard_pads = set()
        adapter.current_track = 0
        adapter.held_step_pad = None
        
        # Add some C note positions for testing
        adapter.keyboard_notes_c = {(5, 0), (7, 0)}
        
        # Check that C notes were identified
        assert len(adapter.keyboard_notes_c) > 0
        
        # Verify C notes are in keyboard rows (4-7)
        for (row, col) in adapter.keyboard_notes_c:
            assert 4 <= row <= 7
            assert 0 <= col <= 7
        
        # Test pad coloring includes keyboard rows
        adapter._update_pad_colors()
        
        # Count calls for keyboard rows
        keyboard_calls = [call for call in adapter.push.pads.set_pad_color.call_args_list 
                         if call[0][0][0] >= 4]  # Keyboard rows
        
        assert len(keyboard_calls) == 32  # 4 rows * 8 cols = 32 keyboard pads
    
    def test_default_pattern_length_is_32(self):
        """Test that new patterns default to 32 steps instead of 16"""
        from sequencer import Pattern, Sequencer
        from unittest.mock import Mock
        
        mock_midi_output = Mock()
        sequencer = Sequencer(mock_midi_output)
        
        # All tracks should default to 32 steps
        for track in sequencer.tracks:
            assert track.length == 32
    
    def test_range_aware_note_filtering_respects_pattern_length(self, setup_ui_sync):
        """Test that range-aware note filtering considers pattern length changes"""
        adapter, sequencer = setup_ui_sync
        
        # Initialize missing attributes
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.current_track = 0
        
        # Set range to 8 steps
        pad1 = (0, 0)  # Step 0
        pad2 = (1, 0)  # Step 8
        adapter.pressed_pads[pad1] = time.time()
        adapter.pressed_pads[pad2] = time.time()
        adapter._process_range_selection()
        
        # Verify both UI and sequencer are at 9 steps
        assert adapter.selected_range_end - adapter.selected_range_start + 1 == 9
        assert sequencer.get_pattern_length(0) == 9
        
        # Test range-aware note system
        adapter._original_add_note = Mock()
        
        # Note within range (step 5) should pass through
        adapter.sequencer.add_note(0, 5, 60, 100)
        assert adapter._original_add_note.called
        
        # Note outside range (step 15) should be filtered
        adapter._original_add_note.reset_mock()
        adapter.sequencer.add_note(0, 15, 62, 100)
        assert not adapter._original_add_note.called
        
        # Note beyond pattern length should also be filtered
        adapter._original_add_note.reset_mock()
        adapter.sequencer.add_note(0, 10, 64, 100)  # Step 10 is beyond pattern length 9
        assert not adapter._original_add_note.called
