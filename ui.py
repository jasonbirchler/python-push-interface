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
            surface = cairo.ImageSurface(cairo.FORMAT_RGB16_565, WIDTH, HEIGHT)
            ctx = cairo.Context(surface)
            
            # Clear background
            ctx.set_source_rgb(0, 0, 0)
            ctx.rectangle(0, 0, WIDTH, HEIGHT)
            ctx.fill()
            
            # Show CC encoder labels and values at TOP
            ctx.set_source_rgb(1, 1, 1)
            ctx.set_font_size(8)
            encoder_width = WIDTH // 8
            cc_count = 0
            for i in range(8):
                encoder_key = f"encoder_{i+1}"
                if hasattr(self, 'cc_values') and encoder_key in self.cc_values:
                    cc_info = self.cc_values[encoder_key]
                    x = i * encoder_width + 2
                    # CC name (truncated if too long)
                    name = cc_info["name"][:10] if len(cc_info["name"]) > 10 else cc_info["name"]
                    ctx.move_to(x, 12)
                    ctx.show_text(name)
                    # CC value
                    ctx.move_to(x, 24)
                    ctx.show_text(str(cc_info["value"]))
                    cc_count += 1

            # Debug: show how many CCs are being displayed
            if cc_count < 8:
                ctx.move_to(10, 35)
                ctx.show_text(f"Showing {cc_count}/8 CCs")

            # Draw title with device info
            ctx.set_font_size(16)
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.move_to(10, 45)

            device = self.device_manager.get_current_device()
            if device:
                ctx.show_text(f"{device.name} - Ch{device.channel}")
            else:
                ctx.show_text("No Device Selected")

            # Show device navigation info
            ctx.set_font_size(12)
            ctx.move_to(10, 65)
            device_info = f"Device {self.device_manager.current_device_index + 1}/{self.device_manager.get_device_count()}"
            ctx.show_text(device_info)

            # Show BPM and play status
            ctx.move_to(10, 85)
            status = "PLAYING" if self.sequencer.is_playing else "STOPPED"
            ctx.show_text(f"BPM: {self.sequencer.bpm} | {status}")

            # Show controls
            ctx.set_font_size(10)
            ctx.move_to(10, 110)
            ctx.show_text("Left/Right: Change Device | Encoders: Adjust CCs")

            # Show octave in bottom right
            ctx.set_font_size(12)
            ctx.move_to(WIDTH - 80, HEIGHT - 10)
            octave_val = self.app_ref.octave if self.app_ref else 4
            ctx.show_text(f"Octave: {octave_val}")

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
