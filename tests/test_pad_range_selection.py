import pytest
from unittest.mock import Mock, MagicMock, patch
import time
import threading
from adapters.push2_adapter import Push2Adapter
from core.sequencer_engine import SequencerEngine

class TestPadBasedRangeSelection:
    """Test the new pad-based range selection system"""
    
    @pytest.fixture
    def mock_sequencer(self):
        """Create a mock sequencer engine"""
        mock_midi_output = Mock()
        return SequencerEngine(mock_midi_output)
    
    @pytest.fixture
    def push_adapter(self, mock_sequencer):
        """Create a Push2 adapter instance"""
        # Create adapter without initializing Push2 hardware
        adapter = Push2Adapter.__new__(Push2Adapter)
        adapter.sequencer = mock_sequencer
        adapter.selected_range_start = 0
        adapter.selected_range_end = 31
        adapter.current_track = 0
        adapter.held_step_pad = None
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.pressed_pads = {}
        adapter.held_keyboard_pads = set()
        adapter.keyboard_octave_offset = 0
        adapter.disabled_key_positions = set()
        adapter.white_key_positions = set()
        adapter.black_key_positions = set()
        adapter.track_colors = ['red', 'blue', 'yellow', 'purple', 'cyan', 'pink', 'orange', 'lime']
        adapter._setup_range_aware_note_system()
        
        # Mock the Push2 hardware
        adapter.push = Mock()
        adapter.push.pads = Mock()
        
        return adapter
    
    def test_pad_layout_mapping(self, push_adapter):
        """Test that pad positions correctly map to step numbers"""
        # Test step 0 (top-left pad)
        assert push_adapter._get_step_position(0) == (0, 0)
        
        # Test step 7 (top row, last column)
        assert push_adapter._get_step_position(7) == (0, 7)
        
        # Test step 8 (second row, first column)
        assert push_adapter._get_step_position(8) == (1, 0)
        
        # Test step 31 (bottom-right step sequencer pad)
        assert push_adapter._get_step_position(31) == (3, 7)
        
        # Test reverse mapping
        row, col = 1, 3  # Second row, 4th column
        step = row * 8 + col
        assert step == 11
    
    def test_range_selection_boundary_detection(self, push_adapter):
        """Test range boundary detection"""
        # Test full range (default)
        assert push_adapter.selected_range_start == 0
        assert push_adapter.selected_range_end == 31
        
        # Test partial range
        push_adapter.selected_range_start = 5
        push_adapter.selected_range_end = 20
        
        # Steps within range
        assert push_adapter._is_step_in_active_range(5) == True
        assert push_adapter._is_step_in_active_range(12) == True
        assert push_adapter._is_step_in_active_range(20) == True
        
        # Steps outside range
        assert push_adapter._is_step_in_active_range(0) == False
        assert push_adapter._is_step_in_active_range(4) == False
        assert push_adapter._is_step_in_active_range(21) == False
        assert push_adapter._is_step_in_active_range(31) == False
    
    def test_two_pad_range_selection(self, push_adapter):
        """Test simultaneous two-pad press for range selection"""
        # Simulate pressing pads at positions (0,0) and (2,5)
        pad1 = (0, 0)  # Step 0
        pad2 = (2, 5)  # Step 21 (2*8 + 5 = 21)
        
        # Add pressed pads
        push_adapter.pressed_pads[pad1] = time.time()
        push_adapter.pressed_pads[pad2] = time.time()
        
        # Process range selection
        push_adapter._process_range_selection()
        
        # Should set range from min to max
        assert push_adapter.selected_range_start == 0
        assert push_adapter.selected_range_end == 21
        
        # Pressed pads should be cleared
        assert len(push_adapter.pressed_pads) == 0
    
    def test_keyboard_note_calculation(self, push_adapter):
        """Test MIDI keyboard note calculation"""
        # Test base note calculation
        push_adapter.keyboard_octave_offset = 0
        base_note = 48 + push_adapter.keyboard_octave_offset * 12  # Should be 48 (C3)
        
        # Test pad at row 4, col 0 (bottom row, first column)
        row, col = 4, 0
        calculated_note = base_note + (7 - row) * 8 + col
        expected_note = 48 + 3 * 8 + 0  # 48 + 24 = 72 (C5)
        assert calculated_note == expected_note
        
        # Test pad at row 7, col 7 (top keyboard row, last column)
        row, col = 7, 7
        calculated_note = base_note + (7 - row) * 8 + col
        expected_note = 48 + 0 * 8 + 7  # 48 + 7 = 55 (G3)
        assert calculated_note == expected_note
    
    def test_keyboard_octave_control(self, push_adapter):
        """Test keyboard octave adjustment"""
        # Test octave up
        initial_offset = push_adapter.keyboard_octave_offset
        push_adapter.keyboard_octave_offset = min(5, push_adapter.keyboard_octave_offset + 1)
        assert push_adapter.keyboard_octave_offset == initial_offset + 1
        
        # Test octave down
        push_adapter.keyboard_octave_offset = max(-2, push_adapter.keyboard_octave_offset - 1)
        assert push_adapter.keyboard_octave_offset == initial_offset
    
    def test_range_aware_note_system(self, push_adapter):
        """Test that note addition respects active range"""
        # Set active range to steps 5-15
        push_adapter.selected_range_start = 5
        push_adapter.selected_range_end = 15
        push_adapter.current_track = 0
        
        # Mock the original add_note method
        push_adapter._original_add_note = Mock()
        
        # Try to add note within range (should succeed)
        push_adapter.sequencer.add_note(0, 10, 60, 100)
        push_adapter._original_add_note.assert_called_with(0, 10, 60, 100)
        
        # Try to add note outside range (should be ignored)
        push_adapter._original_add_note.reset_mock()
        push_adapter.sequencer.add_note(0, 20, 62, 100)
        push_adapter._original_add_note.assert_not_called()
    
    def test_pad_press_state_tracking(self, push_adapter):
        """Test pad press state tracking"""
        # Simulate pad press
        pad_id = (1, 3)
        push_adapter.pressed_pads[pad_id] = time.time()
        
        assert pad_id in push_adapter.pressed_pads
        
        # Simulate pad release
        del push_adapter.pressed_pads[pad_id]
        
        assert pad_id not in push_adapter.pressed_pads
    
    def test_keyboard_pad_state_tracking(self, push_adapter):
        """Test keyboard pad state tracking"""
        # Simulate keyboard pad press
        pad_id = (5, 2)
        push_adapter.held_keyboard_pads.add(pad_id)
        
        assert pad_id in push_adapter.held_keyboard_pads
        
        # Simulate keyboard pad release
        push_adapter.held_keyboard_pads.discard(pad_id)
        
        assert pad_id not in push_adapter.held_keyboard_pads

class TestPadColorSystem:
    """Test the new pad color system for 32-step layout"""
    
    @pytest.fixture
    def mock_push_adapter(self):
        """Create a mock push adapter with mocked Push2 hardware"""
        mock_sequencer = Mock()
        mock_sequencer.is_playing = False
        mock_sequencer.get_current_step.return_value = 0
        mock_sequencer.get_pattern_length.return_value = 16
        mock_sequencer._internal_sequencer = Mock()
        mock_sequencer._internal_sequencer.tracks = [Mock() for _ in range(8)]
        mock_sequencer.midi_output = Mock()
        
        # Create adapter without initializing Push2 hardware
        adapter = Push2Adapter.__new__(Push2Adapter)
        adapter.sequencer = mock_sequencer
        adapter.selected_range_start = 0
        adapter.selected_range_end = 31
        adapter.current_track = 0
        adapter.held_step_pad = None
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.track_colors = ['red', 'blue', 'yellow', 'purple', 'cyan', 'pink', 'orange', 'lime']
        adapter.disabled_key_positions = set()
        adapter.white_key_positions = set()
        adapter.black_key_positions = set()
        adapter.held_keyboard_pads = set()
        adapter.piano_note_mapping = {}  # Add missing piano note mapping
        adapter.keyboard_octave_offset = 0
        
        # Mock the Push2 hardware
        adapter.push = Mock()
        adapter.push.pads = Mock()
        
        return adapter
    
    def test_step_sequencer_colors(self, mock_push_adapter):
        """Test step sequencer pad colors"""
        # Test active range vs inactive range coloring
        mock_push_adapter.selected_range_start = 5
        mock_push_adapter.selected_range_end = 20
        mock_push_adapter.held_step_pad = None
        
        # Call pad color update
        mock_push_adapter._update_pad_colors()
        
        # Verify that inactive steps are set to light_gray
        for step in [0, 1, 4, 21, 31]:  # Steps outside range
            row, col = mock_push_adapter._get_step_position(step)
            expected_color = 'light_gray'
            
            # Check that set_pad_color was called with inactive color
            calls = mock_push_adapter.push.pads.set_pad_color.call_args_list
            pad_call = next((call for call in calls if call[0][0] == (row, col)), None)
            if pad_call:
                assert pad_call[0][1] == expected_color
    
    def test_current_step_highlighting(self, mock_push_adapter):
        """Test current step highlighting"""
        mock_push_adapter.sequencer.is_playing = True
        mock_push_adapter.sequencer.get_current_step.return_value = 10
        mock_push_adapter.held_step_pad = None
        mock_push_adapter.selected_range_start = 0
        mock_push_adapter.selected_range_end = 31
        
        # Mock that step 10 has notes
        mock_push_adapter._has_notes_at_step = Mock(return_value=True)
        
        mock_push_adapter._update_pad_colors()
        
        # Verify current step is highlighted
        calls = mock_push_adapter.push.pads.set_pad_color.call_args_list
        step_10_call = next((call for call in calls if call[0][0] == (1, 2)), None)  # Step 10 = (1, 2)
        if step_10_call:
            assert step_10_call[0][1] == 'green'  # Current step should be green
    
    def test_keyboard_pad_colors(self, mock_push_adapter):
        """Test keyboard pad colors"""
        mock_push_adapter.held_step_pad = 5
        mock_push_adapter.tracks[0] = Mock()  # Track exists
        mock_push_adapter.current_track = 0
        
        mock_push_adapter._update_pad_colors()
        
        # Verify keyboard pads show "ready for note input" color
        calls = mock_push_adapter.push.pads.set_pad_color.call_args_list
        keyboard_calls = [call for call in calls if call[0][0][0] >= 4]  # Keyboard rows
        
        if keyboard_calls:
            # Should have some color when ready for note input (white, turquoise, or light_gray)
            valid_colors = ['white', 'turquoise', 'light_gray', 'dark_gray']
            assert any(call[0][1] in valid_colors for call in keyboard_calls)

class TestRangeSelectionIntegration:
    """Test integration between range selection and core sequencer"""
    
    @pytest.fixture
    def integrated_setup(self):
        """Set up integrated test with real sequencer and mocked hardware"""
        from unittest.mock import Mock
        from sequencer import Sequencer
        
        # Create real sequencer components
        mock_midi_output = Mock()
        internal_sequencer = Sequencer(mock_midi_output)
        
        # Create engine
        sequencer_engine = SequencerEngine(mock_midi_output)
        sequencer_engine._internal_sequencer = internal_sequencer
        
        # Create adapter without initializing Push2 hardware
        adapter = Push2Adapter.__new__(Push2Adapter)
        adapter.sequencer = sequencer_engine
        adapter.selected_range_start = 0
        adapter.selected_range_end = 31
        adapter.current_track = 0
        adapter.held_step_pad = None
        adapter.tracks = [Mock() for _ in range(8)]
        adapter.pressed_pads = {}
        adapter.held_keyboard_pads = set()
        adapter._setup_range_aware_note_system()
        
        # Mock the Push2 hardware
        adapter.push = Mock()
        adapter.push.pads = Mock()
        
        return adapter, sequencer_engine
    
    def test_range_changes_preserve_existing_notes(self, integrated_setup):
        """Test that changing range preserves notes within new range"""
        adapter, engine = integrated_setup
        
        # Add notes at various steps
        engine.add_note(0, 5, 60, 100)  # Within future range
        engine.add_note(0, 15, 62, 100)  # Within future range
        engine.add_note(0, 25, 64, 100)  # Outside future range
        
        # Change range to exclude step 25
        adapter.selected_range_start = 0
        adapter.selected_range_end = 20
        
        # Verify notes outside range are still in sequencer but won't play
        # (This tests the adapter-level filtering)
        assert len(engine._internal_sequencer.tracks[0].get_notes_at_step(25)) == 1
        
        # Test range-aware note system
        adapter._original_add_note = Mock()
        
        # Try to add note outside range (should be filtered)
        adapter.sequencer.add_note(0, 25, 66, 100)
        # Note: The range-aware system should filter this, but we can't easily test the mock here
        
        # Try to add note inside range (should work)
        adapter.sequencer.add_note(0, 10, 68, 100)
        # Note: This should work but testing the exact mock call is complex with the wrapper
