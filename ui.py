import push2_python
import cairo
import numpy

class SequencerUI:
    def __init__(self, sequencer):
        self.sequencer = sequencer
        self.current_page = 'pattern'
        self.selected_step = 0
        
    def generate_pattern_display(self):
        WIDTH, HEIGHT = push2_python.constants.DISPLAY_LINE_PIXELS, push2_python.constants.DISPLAY_N_LINES
        surface = cairo.ImageSurface(cairo.FORMAT_RGB16_565, WIDTH, HEIGHT)
        ctx = cairo.Context(surface)
        
        # Clear background
        ctx.set_source_rgb(0, 0, 0)
        ctx.rectangle(0, 0, WIDTH, HEIGHT)
        ctx.fill()
        
        # Draw title
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_font_size(16)
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.move_to(10, 20)
        ctx.show_text(f"Pattern - Channel {self.sequencer.midi_channel}")
        
        # Draw step indicators
        step_width = WIDTH // 16
        for i in range(16):
            x = i * step_width
            y = 40
            
            # Highlight current playing step
            if i == self.sequencer.current_step and self.sequencer.is_playing:
                ctx.set_source_rgb(1, 0, 0)
            # Highlight selected step
            elif i == self.selected_step:
                ctx.set_source_rgb(0, 1, 0)
            # Show steps with notes
            elif self.sequencer.pattern.get_notes_at_step(i):
                ctx.set_source_rgb(0, 0.5, 1)
            else:
                ctx.set_source_rgb(0.3, 0.3, 0.3)
                
            ctx.rectangle(x + 2, y, step_width - 4, 20)
            ctx.fill()
            
            # Step number
            ctx.set_source_rgb(1, 1, 1)
            ctx.set_font_size(10)
            ctx.move_to(x + 5, y + 15)
            ctx.show_text(str(i + 1))
        
        # Show selected step info
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_font_size(12)
        ctx.move_to(10, 80)
        ctx.show_text(f"Selected Step: {self.selected_step + 1}")
        
        # Show notes at selected step
        notes_at_step = self.sequencer.pattern.get_notes_at_step(self.selected_step)
        if notes_at_step:
            note_names = [self._note_to_name(note.note) for note in notes_at_step]
            ctx.move_to(10, 100)
            ctx.show_text(f"Notes: {', '.join(note_names)}")
        
        # Show BPM and play status
        ctx.move_to(10, 120)
        status = "PLAYING" if self.sequencer.is_playing else "STOPPED"
        ctx.show_text(f"BPM: {self.sequencer.bpm} | {status}")
        
        # Convert to numpy array
        buf = surface.get_data()
        frame = numpy.ndarray(shape=(HEIGHT, WIDTH), dtype=numpy.uint16, buffer=buf)
        return frame.transpose()
        
    def _note_to_name(self, note_num):
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_num // 12) - 1
        note_name = notes[note_num % 12]
        return f"{note_name}{octave}"
        
    def get_current_frame(self):
        if self.current_page == 'pattern':
            return self.generate_pattern_display()
        return self.generate_pattern_display()  # Default fallback