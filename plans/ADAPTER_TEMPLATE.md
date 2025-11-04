# Building a New UI Adapter

This guide shows how to create a new UI adapter for your decoupled sequencer.

## Quick Start

### 1. Create Your Adapter File

Create `adapters/your_adapter.py`:

```python
from adapters.ui_adapter import UIAdapter
from core.sequencer_event_bus import SequencerEventBus

class YourAdapter(UIAdapter):
    """Your custom UI adapter"""
    
    def __init__(self, sequencer):
        super().__init__(sequencer)
        # Initialize your UI here
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize UI components"""
        pass
    
    def run(self):
        """Start the UI event loop"""
        pass
    
    def handle_button_press(self, button_id):
        """Handle button input"""
        pass
    
    def handle_encoder_turn(self, encoder_id, direction):
        """Handle encoder input"""
        pass
    
    def update_display(self, state):
        """Update UI display"""
        pass
```

### 2. Use It in main.py

```python
from core.sequencer_engine import SequencerEngine
from adapters.your_adapter import YourAdapter
from midi_output import MidiOutput

midi = MidiOutput()
sequencer = SequencerEngine(midi)
ui = YourAdapter(sequencer)
ui.run()
```

## Example: Web Adapter

Here's a complete example of a web-based adapter using Flask:

```python
# adapters/web_adapter.py
from adapters.ui_adapter import UIAdapter
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import threading

class WebAdapter(UIAdapter):
    """Web-based UI adapter using Flask"""
    
    def __init__(self, sequencer, host='localhost', port=5000):
        super().__init__(sequencer)
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
        self.setup_event_handlers()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/state', methods=['GET'])
        def get_state():
            """Get current sequencer state"""
            return jsonify({
                'playing': self.sequencer.is_playing,
                'bpm': self.sequencer.bpm,
                'current_step': self.sequencer.current_step,
                'current_track': self.sequencer.current_track,
            })
        
        @self.app.route('/api/play', methods=['POST'])
        def play():
            """Start playback"""
            self.sequencer.play()
            return jsonify({'status': 'ok'})
        
        @self.app.route('/api/stop', methods=['POST'])
        def stop():
            """Stop playback"""
            self.sequencer.stop()
            return jsonify({'status': 'ok'})
        
        @self.app.route('/api/bpm', methods=['POST'])
        def set_bpm():
            """Set BPM"""
            data = request.json
            self.sequencer.set_bpm(data['bpm'])
            return jsonify({'status': 'ok'})
        
        @self.app.route('/api/note', methods=['POST'])
        def add_note():
            """Add a note"""
            data = request.json
            self.sequencer.add_note(
                track=data['track'],
                step=data['step'],
                pitch=data['pitch'],
                velocity=data['velocity']
            )
            return jsonify({'status': 'ok'})
    
    def setup_event_handlers(self):
        """Subscribe to sequencer events"""
        self.bus.subscribe('sequencer:started', self.on_sequencer_started)
        self.bus.subscribe('sequencer:stopped', self.on_sequencer_stopped)
        self.bus.subscribe('sequencer:step_changed', self.on_step_changed)
    
    def on_sequencer_started(self, event):
        """Handle sequencer start"""
        print("Sequencer started")
    
    def on_sequencer_stopped(self, event):
        """Handle sequencer stop"""
        print("Sequencer stopped")
    
    def on_step_changed(self, event):
        """Handle step change"""
        print(f"Step: {event.data['step']}")
    
    def run(self):
        """Start Flask server"""
        print(f"Starting web server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)
    
    def handle_button_press(self, button_id):
        """Handle button press (not used in web)"""
        pass
    
    def handle_encoder_turn(self, encoder_id, direction):
        """Handle encoder turn (not used in web)"""
        pass
    
    def update_display(self, state):
        """Update display (handled by web client)"""
        pass
```

## Example: CLI Adapter

Here's a command-line interface adapter:

```python
# adapters/cli_adapter.py
from adapters.ui_adapter import UIAdapter
import cmd
import threading

class CLIAdapter(UIAdapter, cmd.Cmd):
    """Command-line interface adapter"""
    
    intro = """
    Sequencer CLI
    Type 'help' for commands
    """
    prompt = "sequencer> "
    
    def __init__(self, sequencer):
        super().__init__(sequencer)
        cmd.Cmd.__init__(self)
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Subscribe to sequencer events"""
        self.bus.subscribe('sequencer:started', self.on_sequencer_started)
        self.bus.subscribe('sequencer:stopped', self.on_sequencer_stopped)
        self.bus.subscribe('sequencer:step_changed', self.on_step_changed)
    
    def on_sequencer_started(self, event):
        print("\n[Sequencer started]")
        self.prompt = "sequencer (playing)> "
    
    def on_sequencer_stopped(self, event):
        print("\n[Sequencer stopped]")
        self.prompt = "sequencer> "
    
    def on_step_changed(self, event):
        step = event.data['step']
        print(f"\r[Step {step:2d}]", end='', flush=True)
    
    def do_play(self, arg):
        """Start playback: play"""
        self.sequencer.play()
    
    def do_stop(self, arg):
        """Stop playback: stop"""
        self.sequencer.stop()
    
    def do_bpm(self, arg):
        """Set BPM: bpm 120"""
        try:
            bpm = int(arg)
            self.sequencer.set_bpm(bpm)
            print(f"BPM set to {bpm}")
        except ValueError:
            print("Invalid BPM")
    
    def do_status(self, arg):
        """Show status: status"""
        print(f"Playing: {self.sequencer.is_playing}")
        print(f"BPM: {self.sequencer.bpm}")
        print(f"Step: {self.sequencer.current_step}")
        print(f"Track: {self.sequencer.current_track}")
    
    def do_add_note(self, arg):
        """Add note: add_note <track> <step> <pitch> <velocity>"""
        try:
            parts = arg.split()
            track, step, pitch, velocity = map(int, parts)
            self.sequencer.add_note(track, step, pitch, velocity)
            print(f"Note added: track={track}, step={step}, pitch={pitch}")
        except (ValueError, IndexError):
            print("Usage: add_note <track> <step> <pitch> <velocity>")
    
    def do_quit(self, arg):
        """Exit: quit"""
        self.sequencer.stop()
        return True
    
    def run(self):
        """Start CLI event loop"""
        self.cmdloop()
    
    def handle_button_press(self, button_id):
        """Not used in CLI"""
        pass
    
    def handle_encoder_turn(self, encoder_id, direction):
        """Not used in CLI"""
        pass
    
    def update_display(self, state):
        """Not used in CLI"""
        pass
```

## Example: Network Adapter (Remote Control)

For controlling the sequencer over the network:

```python
# adapters/network_adapter.py
from adapters.ui_adapter import UIAdapter
import socket
import json
import threading

class NetworkAdapter(UIAdapter):
    """Network adapter for remote control"""
    
    def __init__(self, sequencer, host='localhost', port=9000):
        super().__init__(sequencer)
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Subscribe to sequencer events"""
        self.bus.subscribe('sequencer:started', self.broadcast_state)
        self.bus.subscribe('sequencer:stopped', self.broadcast_state)
        self.bus.subscribe('sequencer:step_changed', self.broadcast_state)
    
    def broadcast_state(self, event):
        """Broadcast state to all connected clients"""
        state = {
            'playing': self.sequencer.is_playing,
            'bpm': self.sequencer.bpm,
            'current_step': self.sequencer.current_step,
            'current_track': self.sequencer.current_track,
        }
        # Send to all connected clients
        message = json.dumps(state) + '\n'
        # Implementation depends on your network protocol
    
    def run(self):
        """Start network server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.running = True
        
        print(f"Network adapter listening on {self.host}:{self.port}")
        
        while self.running:
            try:
                client, addr = self.socket.accept()
                print(f"Client connected: {addr}")
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except Exception as e:
                print(f"Error: {e}")
    
    def handle_client(self, client):
        """Handle client connection"""
        try:
            while self.running:
                data = client.recv(1024).decode()
                if not data:
                    break
                
                command = json.loads(data)
                self.process_command(command)
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            client.close()
    
    def process_command(self, command):
        """Process incoming command"""
        cmd = command.get('command')
        
        if cmd == 'play':
            self.sequencer.play()
        elif cmd == 'stop':
            self.sequencer.stop()
        elif cmd == 'set_bpm':
            self.sequencer.set_bpm(command['bpm'])
        elif cmd == 'add_note':
            self.sequencer.add_note(
                track=command['track'],
                step=command['step'],
                pitch=command['pitch'],
                velocity=command['velocity']
            )
    
    def handle_button_press(self, button_id):
        """Not used in network adapter"""
        pass
    
    def handle_encoder_turn(self, encoder_id, direction):
        """Not used in network adapter"""
        pass
    
    def update_display(self, state):
        """Not used in network adapter"""
        pass
```

## Testing Your Adapter

```python
# test_my_adapter.py
from core.sequencer_engine import SequencerEngine
from adapters.your_adapter import YourAdapter
from midi_output import MidiOutput

def test_adapter():
    """Test your adapter"""
    midi = MidiOutput()
    sequencer = SequencerEngine(midi)
    adapter = YourAdapter(sequencer)
    
    # Test basic functionality
    assert adapter.sequencer == sequencer
    assert adapter.bus is not None
    
    # Test event subscription
    events = []
    def capture_event(event):
        events.append(event)
    
    adapter.bus.subscribe('sequencer:started', capture_event)
    sequencer.play()
    
    assert len(events) > 0
    print("✓ Adapter tests passed")

if __name__ == '__main__':
    test_adapter()
```

## Key Patterns

### 1. Event Subscription

```python
def setup_event_handlers(self):
    self.bus.subscribe('sequencer:started', self.on_started)
    self.bus.subscribe('sequencer:stopped', self.on_stopped)
    self.bus.subscribe('sequencer:step_changed', self.on_step_changed)

def on_started(self, event):
    # Update UI to show playing state
    pass
```

### 2. Command Handling

```python
def handle_button_press(self, button_id):
    if button_id == 'play':
        self.sequencer.play()
    elif button_id == 'stop':
        self.sequencer.stop()
    elif button_id == 'add_track':
        # Add track logic
        pass
```

### 3. State Queries

```python
def update_display(self, state):
    # Query current state
    playing = self.sequencer.is_playing
    bpm = self.sequencer.bpm
    step = self.sequencer.current_step
    
    # Update UI
    self.display.show_status(playing, bpm, step)
```

## Common Mistakes to Avoid

1. **Don't modify sequencer state directly**
   ```python
   # ❌ Wrong
   self.sequencer.bpm = 120
   
   # ✅ Correct
   self.sequencer.set_bpm(120)
   ```

2. **Don't block the event loop**
   ```python
   # ❌ Wrong
   while True:
       time.sleep(1)  # Blocks everything
   
   # ✅ Correct
   threading.Thread(target=self.background_task).start()
   ```

3. **Don't forget to subscribe to events**
   ```python
   # ❌ Wrong
   def __init__(self, sequencer):
       super().__init__(sequencer)
       # No event subscriptions
   
   # ✅ Correct
   def __init__(self, sequencer):
       super().__init__(sequencer)
       self.setup_event_handlers()
   ```

4. **Don't assume state without querying**
   ```python
   # ❌ Wrong
   if self.is_playing:  # Undefined
       pass
   
   # ✅ Correct
   if self.sequencer.is_playing:
       pass
   ```

## Next Steps

1. Choose your UI platform (web, CLI, iOS, etc.)
2. Copy the appropriate example above
3. Customize for your needs
4. Test with `python -m pytest`
5. Run with `python main.py`

## Questions?

Refer to:
- [`adapters/ui_adapter.py`](adapters/ui_adapter.py) - Base class
- [`adapters/push2_adapter.py`](adapters/push2_adapter.py) - Reference implementation
- [`core/sequencer_engine.py`](core/sequencer_engine.py) - API documentation
- [`DECOUPLING_COMPLETE.md`](DECOUPLING_COMPLETE.md) - Architecture overview
