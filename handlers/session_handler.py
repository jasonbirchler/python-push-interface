import time

class SessionHandler:
    def __init__(self, app):
        self.app = app
        
    def handle_session_button(self):
        """Handle session button press to toggle session mode"""
        self.app.session_mode = not self.app.session_mode
        
        if self.app.session_mode:
            print("Session mode enabled")
            self.app.last_encoder_time = time.time()
        else:
            print("Session mode disabled")
            self.app.session_action = None
            
    def handle_open_project(self):
        """Handle open project button (Upper Row 1)"""
        if self.app.session_mode:
            self.app.session_action = 'open'
            self.app.session_project_index = 0
            print("Session: Open project selected")
            
    def handle_save_project(self):
        """Handle save project button (Upper Row 2)"""
        if self.app.session_mode:
            self.app.session_action = 'save'
            print("Session: Save project selected")
            
    def handle_save_new_project(self):
        """Handle save new project button (Upper Row 3)"""
        if self.app.session_mode:
            self.app.session_action = 'save_new'
            print("Session: Save new project selected")
            
    def handle_confirm_session_action(self):
        """Handle session action confirmation (OK button)"""
        if self.app.session_mode and self.app.session_action:
            self.app._execute_session_action()
            print(f"Session action executed: {self.app.session_action}")