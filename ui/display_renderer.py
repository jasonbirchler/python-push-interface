import push2_python
import cairo
import numpy

class DisplayRenderer:
    def __init__(self):
        self.WIDTH = push2_python.constants.DISPLAY_LINE_PIXELS
        self.HEIGHT = push2_python.constants.DISPLAY_N_LINES
        self.BUTTON_WIDTH = self.WIDTH // 8
        self.BUTTON_LABEL_PADDING = 5
        self.FONT_SIZE_SMALL = 12
        self.FONT_SIZE_MED = 18
        self.FONT_SIZE_LARGE = 36
        
    def _trim_device_name(self, name):
        """Trim device name at first space to keep display clean"""
        trimmed_name = name
        words = name.split(' ')
        if len(words) > 1:
            trimmed_name = ' '.join(words[:2])
        return trimmed_name
    
    def _note_to_name(self, note_num):
        """Convert MIDI note number to note name"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_num // 12) - 1
        note_name = notes[note_num % 12]
        return f"{note_name}{octave}"
        
    def create_surface(self):
        """Create and setup Cairo surface"""
        surface = cairo.ImageSurface(cairo.FORMAT_RGB16_565, self.WIDTH, self.HEIGHT)
        ctx = cairo.Context(surface)
        # Clear background
        ctx.set_source_rgb(0, 0, 0)
        ctx.rectangle(0, 0, self.WIDTH, self.HEIGHT)
        ctx.fill()
        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        return surface, ctx
        
    def surface_to_frame(self, surface):
        """Convert Cairo surface to Push2 frame"""
        buf = surface.get_data()
        frame = numpy.ndarray(shape=(self.HEIGHT, self.WIDTH), dtype=numpy.uint16, buffer=buf)
        return frame.transpose()
        
    def render_device_selection(self, ui_state, device_manager, current_track):
        """Render device selection interface"""
        surface, ctx = self.create_surface()
        
        # Title
        ctx.set_font_size(self.FONT_SIZE_MED)
        ctx.move_to(10, 55)
        if ui_state.track_edit_mode and ui_state.held_track_button is not None:
            ctx.show_text(f"Edit track {ui_state.held_track_button+1}")
        else:
            ctx.show_text(f"Select device for track {current_track+1}")
        
        # Current device info
        device = device_manager.get_device_by_index(ui_state.device_selection_index)
        if device:
            ctx.set_font_size(self.FONT_SIZE_MED)
            ctx.move_to(10, 75)
            ctx.show_text(f"{self._trim_device_name(device.name)} (Ch {device.channel})")
        
        # Button labels
        ctx.set_font_size(self.FONT_SIZE_SMALL)
        ctx.move_to(5, 12)
        ctx.show_text("Devices")
        ctx.move_to(self.BUTTON_WIDTH + self.BUTTON_LABEL_PADDING, 12)
        ctx.show_text("Channel")
        ctx.move_to(self.BUTTON_WIDTH * 7 + self.BUTTON_LABEL_PADDING, 12)
        ctx.show_text("OK")
        
        return self.surface_to_frame(surface)
        
    def render_clock_selection(self, ui_state, clock_sources):
        """Render clock selection interface"""
        surface, ctx = self.create_surface()
        
        ctx.set_font_size(self.FONT_SIZE_MED)
        ctx.move_to(10, 65)
        ctx.show_text("Select Clock Source")
        
        clock_source = clock_sources[ui_state.clock_selection_index]
        ctx.set_font_size(self.FONT_SIZE_SMALL)
        ctx.move_to(10, 85)
        ctx.show_text(f"{clock_source}")
        
        ctx.move_to(self.BUTTON_WIDTH * 7 + self.BUTTON_LABEL_PADDING, 12)
        ctx.show_text("OK")
        
        return self.surface_to_frame(surface)
        
    def render_session_mode(self, ui_state, project_manager):
        """Render session management interface"""
        surface, ctx = self.create_surface()
        
        # Button labels
        ctx.set_font_size(self.FONT_SIZE_SMALL)
        ctx.move_to(5, 12)
        ctx.show_text("Open")
        ctx.move_to(5, 22)
        ctx.show_text("project")
        
        ctx.move_to(self.BUTTON_WIDTH + self.BUTTON_LABEL_PADDING, 12)
        ctx.show_text("Save")
        
        ctx.move_to(self.BUTTON_WIDTH * 2 + self.BUTTON_LABEL_PADDING, 12)
        ctx.show_text("Save")
        ctx.move_to(self.BUTTON_WIDTH * 2 + self.BUTTON_LABEL_PADDING, 22)
        ctx.show_text("new")
        
        ctx.move_to(self.BUTTON_WIDTH * 7 + self.BUTTON_LABEL_PADDING, 12)
        ctx.show_text("OK")
        
        # Title
        ctx.set_font_size(self.FONT_SIZE_MED)
        ctx.move_to(10, 50)
        ctx.show_text("Session Options")
        
        # Current action
        ctx.set_font_size(self.FONT_SIZE_SMALL)
        ctx.move_to(10, 85)
        if ui_state.session_action == 'open':
            projects = project_manager.list_projects()
            if projects:
                project_name = projects[ui_state.session_project_index]
                ctx.show_text(f"Open: {project_name}")
        elif ui_state.session_action == 'save':
            if project_manager.current_project_file:
                ctx.show_text(f"Save: {project_manager.current_project_file}")
            else:
                ctx.show_text("Save: New project")
        elif ui_state.session_action == 'save_new':
            ctx.show_text("Save as new project")
        
        return self.surface_to_frame(surface)
        
    def render_main_display(self, sequencer, device_manager, tracks, current_track, cc_values, octave, midi_output, app_ref=None):
        """Render main sequencer display"""
        surface, ctx = self.create_surface()
        
        # CC encoder labels and values
        ctx.set_font_size(self.FONT_SIZE_SMALL)
        for i in range(8):
            encoder_key = f"encoder_{i+1}"
            if encoder_key in cc_values:
                cc_info = cc_values[encoder_key]
                x = i * (self.WIDTH // 8) + 10
                name = cc_info["name"][:10] if len(cc_info["name"]) > 10 else cc_info["name"]
                ctx.move_to(x, 12)
                ctx.show_text(name)
                ctx.move_to(x, 24)
                ctx.show_text(str(cc_info["value"]))
        
        # Track info
        ctx.set_font_size(self.FONT_SIZE_MED)
        ctx.move_to(10, 55)
        
        if tracks[current_track] is not None:
            device = tracks[current_track]
            ctx.show_text(f"Track {current_track+1} - {self._trim_device_name(device.name)} - Ch{device.channel}")
        else:
            ctx.show_text(f"Press Add Track to get started")
        
        # Status info
        ctx.move_to(10, 85)
        status = "PLAYING" if sequencer.is_playing else "STOPPED"
        clock_source = midi_output.selected_clock_source or "Internal"
        ctx.show_text(f"Clock: {clock_source} | BPM: {sequencer.bpm} | {status}")
        
        # Step note information (bottom left)
        if (app_ref and hasattr(app_ref, 'held_step_pad') and 
            app_ref.held_step_pad is not None and 
            tracks[current_track] is not None):
            
            step = app_ref.held_step_pad
            pattern = sequencer.tracks[current_track]
            notes = pattern.get_notes_at_step(step)
            
            ctx.set_font_size(self.FONT_SIZE_SMALL)
            y_pos = self.HEIGHT - 25
            
            if notes and len(notes) > 0:
                for i, note in enumerate(notes):
                    if hasattr(note, 'note') and hasattr(note, 'velocity'):
                        note_name = self._note_to_name(note.note)
                        ctx.move_to(10, y_pos + i * 12)
                        ctx.show_text(f"Step {step}: {note_name} ({note.note}) Vel:{note.velocity}")
            else:
                ctx.move_to(10, y_pos)
                ctx.show_text(f"Step {step}: (empty)")
        
        # Octave
        ctx.move_to(self.WIDTH - 80, self.HEIGHT - 10)
        ctx.show_text(f"Oct: {octave}")
        
        return self.surface_to_frame(surface)
