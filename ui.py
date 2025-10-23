import push2_python
import cairo
import numpy

class SequencerUI:
    def __init__(self, sequencer, device_manager):
        self.sequencer = sequencer
        self.device_manager = device_manager
        self.current_page = 'pattern'
        self.selected_step = 0
        self.octave = 4
        self.cc_values = {}
        self.app_ref = None  # Reference to main app for octave access
        
    def generate_pattern_display(self):
        try:
            WIDTH, HEIGHT = push2_python.constants.DISPLAY_LINE_PIXELS, push2_python.constants.DISPLAY_N_LINES
            BUTTON_WIDTH = WIDTH // 8
            ENCODER_WIDTH = BUTTON_WIDTH
            BUTTON_LABEL_PADDING = 5
            FONT_SIZE_SMALL = 12
            FONT_SIZE_MED = 18
            FONT_SIZE_LARGE = 36
            surface = cairo.ImageSurface(cairo.FORMAT_RGB16_565, WIDTH, HEIGHT)
            ctx = cairo.Context(surface)
            
            # Clear background
            ctx.set_source_rgb(0, 0, 0)
            ctx.rectangle(0, 0, WIDTH, HEIGHT)
            ctx.fill()
            
            ctx.set_source_rgb(1, 1, 1)
            current_track = self.app_ref.current_track if self.app_ref else 0
            
            # Check if we're in device selection mode
            if hasattr(self.app_ref, 'device_selection_mode') and self.app_ref.device_selection_mode:
                # Show ONLY device selection interface
                ctx.set_font_size(FONT_SIZE_MED)
                ctx.move_to(10, 45)
                if (hasattr(self.app_ref, 'track_edit_mode') and self.app_ref.track_edit_mode and 
                    self.app_ref.held_track_button is not None):
                    ctx.show_text(f"EDIT TRACK {self.app_ref.held_track_button+1}")
                else:
                    ctx.show_text(f"SELECT DEVICE FOR TRACK {current_track+1}")
                
                device = self.device_manager.get_device_by_index(self.app_ref.device_selection_index)
                if device:
                    ctx.set_font_size(FONT_SIZE_MED)
                    ctx.move_to(10, 65)
                    ctx.show_text(f"{device.name} (Ch {device.channel})")
                    ctx.set_font_size(FONT_SIZE_SMALL)
                    ctx.move_to(10, 85)

                # Button 1 - Scroll devices
                ctx.set_font_size(FONT_SIZE_SMALL)
                ctx.move_to(5, 12)
                ctx.show_text("Devices")

                # Button 2 - MIDI Channel
                ctx.set_font_size(FONT_SIZE_SMALL)
                ctx.move_to(BUTTON_WIDTH + BUTTON_LABEL_PADDING, 12)
                ctx.show_text("Channel")

                # Button 8 - OK
                ctx.set_font_size(FONT_SIZE_SMALL)
                ctx.move_to(BUTTON_WIDTH * 7 + BUTTON_LABEL_PADDING, 12)
                ctx.show_text("OK")

                # Return early to avoid showing other info
                buf = surface.get_data()
                frame = numpy.ndarray(shape=(HEIGHT, WIDTH), dtype=numpy.uint16, buffer=buf)
                return frame.transpose()

            elif hasattr(self.app_ref, 'clock_selection_mode') and self.app_ref.clock_selection_mode:
                # Show ONLY clock source selection interface
                ctx.set_font_size(FONT_SIZE_MED)
                ctx.move_to(10, 65)
                ctx.show_text("SELECT CLOCK SOURCE")
                
                clock_source = self.app_ref.midi_output.clock_sources[self.app_ref.clock_selection_index]
                ctx.set_font_size(FONT_SIZE_SMALL)
                ctx.move_to(10, 85)
                ctx.show_text(f"{clock_source}")
                ctx.move_to(10, 105)

                ctx.move_to(BUTTON_WIDTH * 7 + BUTTON_LABEL_PADDING, 12)
                ctx.show_text("OK")

                # Return early to avoid showing other info
                buf = surface.get_data()
                frame = numpy.ndarray(shape=(HEIGHT, WIDTH), dtype=numpy.uint16, buffer=buf)
                return frame.transpose()

            elif hasattr(self.app_ref, 'session_mode') and self.app_ref.session_mode:
                # Show session management interface
                # Show button labels at TOP (like CC controls)
                ctx.set_font_size(FONT_SIZE_SMALL)
                
                # Button 1 - Open
                ctx.move_to(5, 12)
                ctx.show_text("Open")
                ctx.move_to(5, 22)
                ctx.show_text("project")
                
                # Button 2 - Save
                ctx.move_to(BUTTON_WIDTH + BUTTON_LABEL_PADDING, 12)
                ctx.show_text("Save")
                
                # Button 3 - Save New
                ctx.move_to(BUTTON_WIDTH * 2 + BUTTON_LABEL_PADDING, 12)
                ctx.show_text("Save")
                ctx.move_to(BUTTON_WIDTH * 2 + BUTTON_LABEL_PADDING, 22)
                ctx.show_text("new")
                
                # Button 8 - OK
                ctx.move_to(BUTTON_WIDTH * 7 + BUTTON_LABEL_PADDING, 12)
                ctx.show_text("OK")
                
                # Show title in middle
                ctx.set_font_size(FONT_SIZE_MED)
                ctx.move_to(10, 50)
                ctx.show_text("SESSION OPTIONS")
                
                # Show current action and project selection
                ctx.set_font_size(FONT_SIZE_SMALL)
                ctx.move_to(10, 85)
                if self.app_ref.session_action == 'open':
                    projects = self.app_ref.project_manager.list_projects()
                    if projects:
                        project_name = projects[self.app_ref.session_project_index]
                        ctx.show_text(f"Open: {project_name}")
                elif self.app_ref.session_action == 'save':
                    if self.app_ref.project_manager.current_project_file:
                        ctx.show_text(f"Save: {self.app_ref.project_manager.current_project_file}")
                    else:
                        ctx.show_text("Save: New project")
                elif self.app_ref.session_action == 'save_new':
                    ctx.show_text("Save as new project")
                
                # Return early to avoid showing other info
                buf = surface.get_data()
                frame = numpy.ndarray(shape=(HEIGHT, WIDTH), dtype=numpy.uint16, buffer=buf)
                return frame.transpose()

            else:
                # Normal mode - show CC encoder labels and values at TOP
                ctx.set_font_size(FONT_SIZE_SMALL)
                cc_count = 0

                for i in range(8):
                    encoder_key = f"encoder_{i+1}"
                    if hasattr(self, 'cc_values') and encoder_key in self.cc_values:
                        cc_info = self.cc_values[encoder_key]
                        x = i * ENCODER_WIDTH + 2
                        # CC name (truncated if too long)
                        name = cc_info["name"][:10] if len(cc_info["name"]) > 10 else cc_info["name"]
                        ctx.move_to(x, 12)
                        ctx.show_text(name)
                        # CC value
                        ctx.move_to(x, 24)
                        ctx.show_text(str(cc_info["value"]))
                        cc_count += 1
                
                # Draw title with track and device info
                ctx.set_font_size(FONT_SIZE_MED)
                ctx.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.move_to(10, 45)
                
                # Normal mode - show current track info
                if hasattr(self.app_ref, 'tracks') and self.app_ref.tracks[current_track] is not None:
                    device = self.app_ref.tracks[current_track]
                    ctx.show_text(f"Track {current_track+1} - {device.name} - Ch{device.channel}")
                else:
                    ctx.show_text(f"Track {current_track+1} - No Device")

            # Show device navigation info (only in normal mode)
            if not (hasattr(self.app_ref, 'device_selection_mode') and self.app_ref.device_selection_mode):
                ctx.set_font_size(FONT_SIZE_SMALL)
                ctx.move_to(10, 65)
                device_info = f"MIDI Ports: {self.device_manager.get_device_count()}"
                ctx.show_text(device_info)

            # Show clock source, BPM and play status
            ctx.move_to(10, 85)
            status = "PLAYING" if self.sequencer.is_playing else "STOPPED"
            clock_source = "Internal"
            if hasattr(self.app_ref, 'midi_output') and self.app_ref.midi_output.selected_clock_source:
                clock_source = self.app_ref.midi_output.selected_clock_source
            ctx.show_text(f"Clock: {clock_source} | BPM: {self.sequencer.bpm} | {status}")
            
            # Show encoder controls info
            ctx.set_font_size(FONT_SIZE_SMALL)
            ctx.move_to(10, 100)
            ctx.show_text("Tempo: BPM | Swing: MIDI Ch | Track 1-8: CC Controls")

            # Show octave in bottom right
            ctx.set_font_size(FONT_SIZE_SMALL)
            ctx.move_to(WIDTH - 80, HEIGHT - 10)
            octave_val = self.app_ref.octave if self.app_ref else 4
            ctx.show_text(f"Oct: {octave_val}")

            # Convert to numpy array
            buf = surface.get_data()
            frame = numpy.ndarray(shape=(HEIGHT, WIDTH), dtype=numpy.uint16, buffer=buf)
            return frame.transpose()

        except Exception as e:
            print(f"Display error: {e}")
            # Return a simple fallback frame
            WIDTH, HEIGHT = push2_python.constants.DISPLAY_LINE_PIXELS, push2_python.constants.DISPLAY_N_LINES
            return numpy.zeros((WIDTH, HEIGHT), dtype=numpy.uint16)

    def _note_to_name(self, note_num):
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_num // 12) - 1
        note_name = notes[note_num % 12]
        return f"{note_name}{octave}"

    def get_current_frame(self):
        if self.current_page == 'pattern':
            return self.generate_pattern_display()
        return self.generate_pattern_display()  # Default fallback
