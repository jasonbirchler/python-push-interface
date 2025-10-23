class UIStateManager:
    def __init__(self):
        # UI Mode states
        self.device_selection_mode = False
        self.clock_selection_mode = False
        self.session_mode = False
        self.track_edit_mode = False
        
        # Selection indices
        self.device_selection_index = 0
        self.clock_selection_index = 0
        self.session_project_index = 0
        
        # Session state
        self.session_action = None  # 'open', 'save', 'save_new'
        
        # Track editing state
        self.held_track_button = None
        
    def enter_device_selection(self, track_num=None):
        """Enter device selection mode"""
        self.device_selection_mode = True
        self.device_selection_index = 0
        
    def enter_track_edit(self, track_num, current_device_index=0):
        """Enter track edit mode"""
        self.track_edit_mode = True
        self.device_selection_mode = True
        self.held_track_button = track_num
        self.device_selection_index = current_device_index
        
    def enter_clock_selection(self):
        """Enter clock selection mode"""
        self.clock_selection_mode = True
        self.clock_selection_index = 0
        
    def enter_session_mode(self):
        """Enter session management mode"""
        self.session_mode = True
        self.session_action = None
        
    def exit_all_modes(self):
        """Exit all special modes"""
        self.device_selection_mode = False
        self.clock_selection_mode = False
        self.session_mode = False
        self.track_edit_mode = False
        self.held_track_button = None
        self.session_action = None
        
    def exit_device_selection(self):
        """Exit device selection mode"""
        self.device_selection_mode = False
        if self.track_edit_mode:
            self.track_edit_mode = False
            self.held_track_button = None
            
    def is_in_special_mode(self):
        """Check if any special mode is active"""
        return (self.device_selection_mode or self.clock_selection_mode or 
                self.session_mode or self.track_edit_mode)