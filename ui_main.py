import push2_python
import cairo
import numpy
from ui.ui_state_manager import UIStateManager
from ui.display_renderer import DisplayRenderer

class SequencerUI:
    def __init__(self, sequencer, device_manager):
        self.sequencer = sequencer
        self.device_manager = device_manager
        self.current_page = 'pattern'
        self.selected_step = 0
        self.octave = 4
        self.cc_values = {}
        self.app_ref = None  # Reference to main app for octave access
        
        # New components
        self.ui_state = UIStateManager()
        self.renderer = DisplayRenderer()
        
    def generate_pattern_display(self):
        try:
            current_track = self.app_ref.current_track if self.app_ref else 0
            
            # Sync UI state with app state
            if self.app_ref:
                self.ui_state.device_selection_mode = getattr(self.app_ref, 'device_selection_mode', False)
                self.ui_state.clock_selection_mode = getattr(self.app_ref, 'clock_selection_mode', False)
                self.ui_state.session_mode = getattr(self.app_ref, 'session_mode', False)
                self.ui_state.track_edit_mode = getattr(self.app_ref, 'track_edit_mode', False)
                self.ui_state.device_selection_index = getattr(self.app_ref, 'device_selection_index', 0)
                self.ui_state.clock_selection_index = getattr(self.app_ref, 'clock_selection_index', 0)
                self.ui_state.session_project_index = getattr(self.app_ref, 'session_project_index', 0)
                self.ui_state.session_action = getattr(self.app_ref, 'session_action', None)
                self.ui_state.held_track_button = getattr(self.app_ref, 'held_track_button', None)
                

            
            # Route to appropriate renderer
            if self.ui_state.device_selection_mode:
                return self.renderer.render_device_selection(
                    self.ui_state, self.device_manager, current_track)
            elif self.ui_state.clock_selection_mode:
                return self.renderer.render_clock_selection(
                    self.ui_state, self.app_ref.midi_output.clock_sources)
            elif self.ui_state.session_mode:
                return self.renderer.render_session_mode(
                    self.ui_state, self.app_ref.project_manager)
            else:
                return self.renderer.render_main_display(
                    self.sequencer, self.device_manager, self.app_ref.tracks,
                    current_track, self.cc_values, self.octave, self.app_ref.midi_output, self.app_ref)

        except Exception as e:
            print(f"Display error: {e}")
            # Return a simple fallback frame
            return numpy.zeros((self.renderer.WIDTH, self.renderer.HEIGHT), dtype=numpy.uint16)

    def _note_to_name(self, note_num):
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_num // 12) - 1
        note_name = notes[note_num % 12]
        return f"{note_name}{octave}"
        
    # Expose UI state for external access
    def get_ui_state(self):
        return self.ui_state

    def get_current_frame(self):
        return self.generate_pattern_display()  # Default fallback
