import push2_python

class TrackHandler:
    def __init__(self, app):
        self.app = app
        
    def handle_track_selection(self, track_num):
        """Handle track button press"""
        if 0 <= track_num < 8 and self.app.tracks[track_num] is not None:
            self.app.held_track_button = track_num
            self.app.current_track = track_num
            print(f"Selected track {track_num}")
            self.app._update_track_buttons()
            self.app._init_cc_values_for_track()
            self.app._update_mute_solo_buttons()
            # Force pad update when switching tracks
            self.app.pad_states = {}
            self.app._update_pad_colors()
            
    def handle_track_release(self):
        """Handle track button release"""
        if not self.app.track_edit_mode:
            self.app.held_track_button = None
            
    def handle_mute(self):
        """Handle mute button press"""
        if self.app.tracks[self.app.current_track] is None:
            return
            
        self.app.track_muted[self.app.current_track] = not self.app.track_muted[self.app.current_track]
        
        if self.app.track_muted[self.app.current_track]:
            print(f"Muted track {self.app.current_track}")
        else:
            print(f"Unmuted track {self.app.current_track}")
            
        self.app._update_mute_solo_buttons()
        
    def handle_solo(self):
        """Handle solo button press"""
        if self.app.tracks[self.app.current_track] is None:
            return
            
        if self.app.solo_mode and self.app.soloed_track == self.app.current_track:
            # Turn off solo
            self.app.solo_mode = False
            self.app.soloed_track = None
            print(f"Solo off - all tracks restored")
        else:
            # Turn on solo
            self.app.solo_mode = True
            self.app.soloed_track = self.app.current_track
            print(f"Solo track {self.app.current_track}")
        self.app._update_mute_solo_buttons()