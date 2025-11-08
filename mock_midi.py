"""Mock MIDI interface for testing and CI environments without ALSA/MIDI support"""

class MockMidiPort:
    """Mock MIDI port that captures messages instead of sending them"""
    def __init__(self, name):
        self.name = name
        self.messages = []
        self.is_closed = False
        
    def send(self, message):
        if not self.is_closed:
            self.messages.append(message)
            
    def close(self):
        self.is_closed = True
        
    def clear_messages(self):
        self.messages.clear()

class MockMidiMessage:
    """Mock MIDI message"""
    def __init__(self, msg_type, **kwargs):
        self.type = msg_type
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def __repr__(self):
        attrs = [f"{k}={v}" for k, v in self.__dict__.items() if k != 'type']
        return f"MockMidiMessage('{self.type}', {', '.join(attrs)})"

class MockMidiInput:
    """Mock MIDI input port"""
    def __init__(self, name):
        self.name = name
        self.callback = None
        self.pending_messages = []
        self.is_closed = False
        
    def iter_pending(self):
        messages = self.pending_messages.copy()
        self.pending_messages.clear()
        return messages
        
    def close(self):
        self.is_closed = True
        
    def inject_message(self, message):
        """Inject a message for testing"""
        if not self.is_closed:
            self.pending_messages.append(message)
            if self.callback:
                self.callback(message)

# Mock mido module functions
def get_output_names():
    """Return mock MIDI output port names"""
    return ["Mock MIDI Out 1", "Mock MIDI Out 2", "Test Device"]

def get_input_names():
    """Return mock MIDI input port names"""
    return ["Mock MIDI In 1", "Mock Clock Source"]

def open_output(name):
    """Return mock MIDI output port"""
    return MockMidiPort(name)

def open_input(name):
    """Return mock MIDI input port"""
    return MockMidiInput(name)

def Message(msg_type, **kwargs):
    """Create mock MIDI message"""
    return MockMidiMessage(msg_type, **kwargs)

# Mock ports module
class MockPorts:
    """Mock ports module"""
    @staticmethod
    def get_output_names():
        return get_output_names()
    
    @staticmethod
    def get_input_names():
        return get_input_names()

ports = MockPorts()

# Mock base classes for mido ports
class BaseInput:
    """Mock base input class"""
    def receive(self, block=True):
        """Mock receive method"""
        return None
    
    def poll(self):
        """Mock poll method"""
        return None
    
    def iter_pending(self):
        """Mock iter_pending method"""
        return []

class BaseOutput:
    """Mock base output class"""
    def send(self, message):
        """Mock send method"""
        pass

# Add base classes to ports module
ports.BaseInput = BaseInput
ports.BaseOutput = BaseOutput