import push2_python
import time

class ClockHandler:
    def __init__(self, app):
        self.app = app
        
    def handle_metronome_button(self):
        """Handle metronome button press to toggle clock selection mode"""
        self.app.clock_selection_mode = not self.app.clock_selection_mode
        
        if self.app.clock_selection_mode:
            print("Clock selection mode enabled")
            self.app.last_encoder_time = time.time()
        else:
            print("Clock selection mode disabled")
            
    def handle_clock_selection_encoder(self, increment):
        """Handle encoder for clock source selection"""
        if self.app.clock_selection_mode:
            clock_sources = self.app.midi_output.clock_sources
            if clock_sources:
                direction = 1 if increment > 0 else -1
                self.app.clock_selection_index = (self.app.clock_selection_index + direction) % len(clock_sources)
                print(f"Clock selection: {self.app.clock_selection_index}")
                self.app.last_encoder_time = time.time()
                
    def handle_confirm_clock_selection(self):
        """Handle clock source confirmation"""
        if self.app.clock_selection_mode:
            clock_sources = self.app.midi_output.clock_sources
            if clock_sources and 0 <= self.app.clock_selection_index < len(clock_sources):
                selected_source = clock_sources[self.app.clock_selection_index]
                self.app.midi_output.select_clock_source(selected_source)
                print(f"Clock source selected: {selected_source}")
            else:
                print("Invalid clock selection index")
            self.app.clock_selection_mode = False