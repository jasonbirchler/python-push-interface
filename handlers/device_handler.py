import push2_python
import time

class DeviceHandler:
    def __init__(self, app):
        self.app = app
        
    def handle_add_track(self):
        """Handle add track button press"""
        self.app.device_selection_mode = not self.app.device_selection_mode

        if self.app.device_selection_mode:
            print(f"Add track button detected")
            self.app.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_8, 'white')
            self._add_track()
        else:
            self.app.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_8, 'white')
            
    def handle_setup(self):
        """Handle setup button press for track editing"""
        if self.app.held_track_button is not None and self.app.tracks[self.app.held_track_button] is not None:
            self._enter_track_edit_mode()
        else:
            print("Hold a track button and press Setup to edit track")
            

                
    def handle_confirm_selection(self):
        """Handle device selection confirmation"""
        if self.app.device_selection_mode:
            device = self.app.device_manager.get_device_by_index(self.app.device_selection_index)
            if device:
                # Try to connect to device port first
                if self.app.midi_output.connect(device.port):
                    target_track = self.app.held_track_button if self.app.track_edit_mode else self.app.current_track
                    self.app.tracks[target_track] = device
                    self.app.sequencer.set_track_channel(target_track, device.channel)
                    self.app.sequencer.set_track_port(target_track, device.port)
                    self.app.sequencer.set_track_device(target_track, device)
                    self.app.device_selection_mode = False
                    
                    if self.app.track_edit_mode:
                        print(f"Track {target_track} updated to {device.name} on port {device.port}")
                        self.app.track_edit_mode = False
                        self.app.held_track_button = None
                    else:
                        print(f"Track {target_track} assigned to {device.name} on port {device.port}")
                        
                    self.app._update_track_buttons()
                    self.app._init_cc_values_for_track()
                    # Force pad update after confirming device
                    self.app.pad_states = {}
                    self.app._update_pad_colors()
                else:
                    print(f"Failed to connect to {device.name} - track not assigned")
                    # Stay in device selection mode to try another device
                    
    def _add_track(self):
        """Find next empty track slot and enter device selection"""
        for i in range(8):
            if self.app.tracks[i] is None:
                self.app.current_track = i
                self.app.device_selection_mode = True
                self.app.device_selection_index = 0
                self.app.encoder_accumulator = 0  # Reset accumulator
                print(f"Adding track {i}, select device... (device_selection_mode = {self.app.device_selection_mode})")
                self.app._update_track_buttons()
                # Force UI update to show device selection
                self.app.last_encoder_time = time.time()
                return
        print("All tracks are full")
        self.app.push.buttons.set_button_color(push2_python.constants.BUTTON_ADD_TRACK, 'black')
        
    def _enter_track_edit_mode(self):
        """Enter edit mode for the held track"""
        self.app.track_edit_mode = True
        self.app.device_selection_mode = True
        self.app.device_selection_index = 0
        
        # Find current device index
        current_device = self.app.tracks[self.app.held_track_button]
        for i, device in enumerate(self.app.device_manager.current_devices):
            if device.name == current_device.name and device.port == current_device.port:
                self.app.device_selection_index = i
                break
                
        # Light up OK button
        self.app.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_8, 'white')
        
        print(f"Editing track {self.app.held_track_button} - {current_device.name}")
        self.app.last_encoder_time = time.time()