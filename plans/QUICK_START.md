# Quick Start Guide: Decoupled Sequencer

## TL;DR

Your sequencer is now decoupled from the UI. The sequencer logic is in `core/sequencer_engine.py` and can work with any UI adapter.

## Run It

```bash
# Run with Push2 simulator
python main.py --simulator

# Run tests
python -m pytest tests/test_core_abstraction.py -v
```

## Use It

```python
from core.sequencer_engine import SequencerEngine
from adapters.push2_adapter import Push2Adapter
from midi_output import MidiOutput

# Create sequencer
midi = MidiOutput()
sequencer = SequencerEngine(midi)

# Create UI
ui = Push2Adapter(sequencer, use_simulator=True)

# Run
ui.run()
```

## Test It (No Hardware)

```python
from core.sequencer_engine import SequencerEngine
from midi_output import MidiOutput

midi = MidiOutput()
sequencer = SequencerEngine(midi)

# Add a note
sequencer.add_note(track=0, step=0, pitch=60, velocity=100)

# Control playback
sequencer.set_bpm(120)
sequencer.play()

# Query state
print(f"Playing: {sequencer.is_playing}")
print(f"BPM: {sequencer.bpm}")
print(f"Step: {sequencer.current_step}")
```

## Build a New UI

```python
from adapters.ui_adapter import UIAdapter

class MyAdapter(UIAdapter):
    def run(self):
        # Your event loop
        pass
    
    def handle_button_press(self, button_id):
        if button_id == 'play':
            self.sequencer.play()
    
    def update_display(self, state):
        # Update UI
        pass
```

Then use it:

```python
sequencer = SequencerEngine(midi)
ui = MyAdapter(sequencer)
ui.run()
```

## File Structure

```
core/
├── sequencer_engine.py      # Pure sequencer logic
├── sequencer_state.py       # Immutable state
└── sequencer_event_bus.py   # Pub/sub events

adapters/
├── ui_adapter.py            # Abstract base
└── push2_adapter.py          # Push2 implementation

handlers/
├── button_manager.py        # Button routing
├── transport_handler.py      # Play/stop
├── session_handler.py        # Save/load
└── ...

ui/
├── display_renderer.py      # Push2 display
└── ui_state_manager.py      # UI state

main.py                       # Entry point
```

## Key APIs

### SequencerEngine

```python
# Playback
sequencer.play()
sequencer.stop()
sequencer.reset_step()

# Configuration
sequencer.set_bpm(120)
sequencer.set_current_track(0)
sequencer.set_track_channel(0, 1)
sequencer.set_track_port(0, "IAC Driver Bus 1")

# Notes
sequencer.add_note(track=0, step=0, pitch=60, velocity=100)
sequencer.remove_note(track=0, step=0, pitch=60)

# State
sequencer.is_playing
sequencer.bpm
sequencer.current_step
sequencer.current_track
sequencer.tracks
```

### SequencerEventBus

```python
# Subscribe
bus.subscribe('sequencer:started', on_started)
bus.subscribe('sequencer:stopped', on_stopped)
bus.subscribe('sequencer:step_changed', on_step_changed)

# Publish
bus.publish('sequencer:started', {})
```

### UIAdapter

```python
class MyAdapter(UIAdapter):
    def run(self):
        """Start UI event loop"""
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

## Examples

### Web UI (Flask)

See [`ADAPTER_TEMPLATE.md`](ADAPTER_TEMPLATE.md) for complete example.

```python
from flask import Flask, jsonify
from adapters.ui_adapter import UIAdapter

class WebAdapter(UIAdapter):
    def __init__(self, sequencer):
        super().__init__(sequencer)
        self.app = Flask(__name__)
        self.setup_routes()
    
    @self.app.route('/api/play', methods=['POST'])
    def play():
        self.sequencer.play()
        return jsonify({'status': 'ok'})
    
    def run(self):
        self.app.run()
```

### CLI Interface

See [`ADAPTER_TEMPLATE.md`](ADAPTER_TEMPLATE.md) for complete example.

```python
import cmd
from adapters.ui_adapter import UIAdapter

class CLIAdapter(UIAdapter, cmd.Cmd):
    def do_play(self, arg):
        """Start playback"""
        self.sequencer.play()
    
    def do_stop(self, arg):
        """Stop playback"""
        self.sequencer.stop()
    
    def run(self):
        self.cmdloop()
```

### Network Adapter (iOS/Remote)

See [`ADAPTER_TEMPLATE.md`](ADAPTER_TEMPLATE.md) for complete example.

```python
import socket
import json
from adapters.ui_adapter import UIAdapter

class NetworkAdapter(UIAdapter):
    def run(self):
        # Start WebSocket server
        # iOS app connects and sends commands
        pass
    
    def process_command(self, command):
        if command['cmd'] == 'play':
            self.sequencer.play()
        elif command['cmd'] == 'stop':
            self.sequencer.stop()
```

## Event Types

```python
# Playback events
'sequencer:started'
'sequencer:stopped'
'sequencer:step_changed'
'sequencer:bpm_changed'

# Track events
'track:note_added'
'track:note_removed'
'track:channel_changed'
'track:port_changed'

# UI events
'ui:mode_changed'
'ui:track_selected'
'ui:display_updated'
```

## Testing

```bash
# Run all tests
python -m pytest tests/test_core_abstraction.py -v

# Expected: 23 passed ✅
```

## Documentation

- **[`DECOUPLING_PROPOSAL_RESPONSE.md`](DECOUPLING_PROPOSAL_RESPONSE.md)** - Complete answer to your question
- **[`DECOUPLING_COMPLETE.md`](DECOUPLING_COMPLETE.md)** - Full architecture guide
- **[`ADAPTER_TEMPLATE.md`](ADAPTER_TEMPLATE.md)** - How to build new UIs
- **[`DECOUPLING_SUMMARY.md`](DECOUPLING_SUMMARY.md)** - Original proposal

## Common Tasks

### Add a Note
```python
sequencer.add_note(track=0, step=0, pitch=60, velocity=100)
```

### Remove a Note
```python
sequencer.remove_note(track=0, step=0, pitch=60)
```

### Change BPM
```python
sequencer.set_bpm(120)
```

### Select Track
```python
sequencer.set_current_track(1)
```

### Set MIDI Output
```python
sequencer.set_track_channel(0, 1)  # Track 0 → MIDI channel 1
sequencer.set_track_port(0, "IAC Driver Bus 1")
```

### Listen to Events
```python
def on_step_changed(event):
    print(f"Step: {event.data['step']}")

sequencer.bus.subscribe('sequencer:step_changed', on_step_changed)
```

### Query State
```python
print(f"Playing: {sequencer.is_playing}")
print(f"BPM: {sequencer.bpm}")
print(f"Step: {sequencer.current_step}")
print(f"Track: {sequencer.current_track}")
```

## Troubleshooting

### Sequencer not responding
1. Check button routing in `handlers/button_manager.py`
2. Verify handler is subscribed to events
3. Check event bus is publishing events

### Display not updating
1. Verify `SequencerUI` is initialized in `Push2Adapter`
2. Check display rendering in `ui/display_renderer.py`
3. Ensure event loop is running

### Tests failing
1. Run: `python -m pytest tests/test_core_abstraction.py -v`
2. Check for import errors
3. Verify dependencies: `pip install -r requirements.txt`

## Next Steps

1. **Verify**: `python -m pytest tests/test_core_abstraction.py -v`
2. **Run**: `python main.py --simulator`
3. **Choose UI**: Web, CLI, iOS, or custom
4. **Build**: Use [`ADAPTER_TEMPLATE.md`](ADAPTER_TEMPLATE.md) as reference
5. **Deploy**: Run your new UI with the sequencer

## Architecture at a Glance

```
SequencerEngine (pure logic)
    ↓
SequencerEventBus (pub/sub)
    ↓
    ├─ Push2Adapter (current)
    ├─ WebAdapter (build it!)
    ├─ CLIAdapter (build it!)
    └─ IOSAdapter (build it!)
```

## Key Concepts

| Concept | Purpose |
|---------|---------|
| **SequencerEngine** | Pure MIDI logic, no UI |
| **SequencerEventBus** | Loose coupling via events |
| **UIAdapter** | Abstract interface for UIs |
| **Concrete Adapters** | Push2, Web, CLI, iOS, etc. |
| **Immutable State** | Predictable state management |

## Status

✅ Sequencer decoupled from UI  
✅ 23 unit tests passing  
✅ Push2 adapter working  
✅ Display rendering working  
✅ Button handling working  
✅ Ready for new UIs  

## Questions?

See the full documentation:
- Architecture: [`DECOUPLING_COMPLETE.md`](DECOUPLING_COMPLETE.md)
- Building UIs: [`ADAPTER_TEMPLATE.md`](ADAPTER_TEMPLATE.md)
- Full Answer: [`DECOUPLING_PROPOSAL_RESPONSE.md`](DECOUPLING_PROPOSAL_RESPONSE.md)

---

**You're ready to go!** 🚀
