import push2_python

class TransportHandler:
    def __init__(self, app):
        self.app = app
        
    def handle_play(self):
        """Handle play button press"""
        if self.app.sequencer.is_playing:
            self.app.sequencer.stop()
            self.app.push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')
        else:
            self.app.sequencer.play()
            self.app.push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'green', 
                                                   push2_python.constants.ANIMATION_PULSING_QUARTER)
            
    def handle_stop(self):
        """Handle stop button press"""
        self.app.sequencer.stop()
        self.app.sequencer.current_step = 0
        self.app.push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, 'white')
        
