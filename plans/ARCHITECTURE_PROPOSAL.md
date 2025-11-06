# Sequencer Decoupling Architecture Proposal

## Executive Summary

Your current architecture tightly couples the MIDI sequencer logic with the Push2 UI. This proposal outlines a complete decoupling strategy using **event-driven architecture** and **adapter pattern**, enabling the sequencer to work with any UI (Push2, web, iOS, CLI, etc.) without modification.

## Current Architecture Problems

### Tight Coupling Issues
1. **Sequencer depends on UI**: `sequencer.py` has callbacks (`_update_pad_colors_callback`) and app references
2. **App orchestrates everything**: `SequencerApp` mixes sequencer logic, UI state, and Push2 handling
3. **Handlers directly manipulate sequencer**: Button handlers directly call sequencer methods
4. **UI state scattered**: Track state, mute/solo, device selection spread across `SequencerApp`
5. **No clear boundaries**: Difficult to test sequencer independently from Push2

### Current Data Flow
```
Push2 Input → SequencerApp → Sequencer → MIDI Output
                    ↓
              UI State Management
                    ↓
              Push2 Display Update
```

## Proposed Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    SEQUENCER CORE                           │
│  (Pure business logic, no UI dependencies)                  │
│  - SequencerEngine                                          │
│  - Pattern/Track management                                 │
│  - MIDI timing & playback                                   │
│  - State management                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐        ┌──────────────────┐
│ SequencerEventBus│        │ SequencerState   │
│ (Pub/Sub)        │        │ (Immutable)      │
│ - Events         │        │ - Read-only      │
│ - Subscribers    │        │ - Snapshots      │
└──────────────────┘        └──────────────────┘
        │                             │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐        ┌──────────────────┐
│  Push2 Adapter   │        │  Web Adapter     │
│  (UI Layer)      │        │  (UI Layer)      │
│ - Button handler │        │ - HTTP/WebSocket │
│ - Pad renderer   │        │ - React state    │
│ - Display update │        │ - REST API       │
└──────────────────┘        └──────────────────┘
        │                             │
        ▼                             ▼
    Push2 Device              Web Browser
```

## Core Components

### 1. SequencerEngine (Core Logic)
**Location**: `core/sequencer_engine.py`

Pure sequencer logic with NO UI dependencies:
- Pattern/track management
- MIDI note scheduling
- Tempo/clock handling
- State queries (getters only)

```python
class SequencerEngine:
    def __init__(self, midi_output: MidiOutput):
        self.midi_output = midi_output
        self.state = SequencerState()
        self.event_bus = SequencerEventBus()
    
    # Commands (state-changing operations)
    def add_note(self, track: int, step: int, note: int, velocity: int) -> None
    def remove_note(self, track: int, step: int) -> None
    def play(self) -> None
    def stop(self) -> None
    def set_bpm(self, bpm: int) -> None
    
    # Queries (read-only)
    def get_state(self) -> SequencerState
    def get_track_notes(self, track: int) -> List[Note]
    def is_playing(self) -> bool
```

### 2. SequencerState (Immutable State)
**Location**: `core/sequencer_state.py`

Read-only snapshot of sequencer state:
```python
@dataclass(frozen=True)
class SequencerState:
    is_playing: bool
    current_step: int
    bpm: int
    tracks: Tuple[Pattern, ...]
    track_channels: Tuple[int, ...]
    current_track: int
    
    # Queries
    def get_notes_at_step(self, track: int, step: int) -> List[Note]
    def get_track_pattern(self, track: int) -> Pattern
```

### 3. SequencerEventBus (Pub/Sub)
**Location**: `core/sequencer_event_bus.py`

Event-driven communication:
```python
class SequencerEventBus:
    def subscribe(self, event_type: str, callback: Callable) -> None
    def unsubscribe(self, event_type: str, callback: Callable) -> None
    def publish(self, event: SequencerEvent) -> None

# Event types
class SequencerEvent:
    STEP_CHANGED = "step_changed"
    NOTE_TRIGGERED = "note_triggered"
    PLAY_STATE_CHANGED = "play_state_changed"
    BPM_CHANGED = "bpm_changed"
    TRACK_CHANGED = "track_changed"
    PATTERN_MODIFIED = "pattern_modified"
```

### 4. UIAdapter (Abstract Interface)
**Location**: `adapters/ui_adapter.py`

Abstract base class for all UI implementations:
```python
class UIAdapter(ABC):
    def __init__(self, sequencer: SequencerEngine):
        self.sequencer = sequencer
        self.sequencer.event_bus.subscribe("*", self.on_sequencer_event)
    
    # UI → Sequencer commands
    @abstractmethod
    def handle_note_input(self, track: int, step: int, note: int) -> None
    @abstractmethod
    def handle_play(self) -> None
    @abstractmethod
    def handle_stop(self) -> None
    
    # Sequencer → UI updates
    @abstractmethod
    def on_sequencer_event(self, event: SequencerEvent) -> None
    @abstractmethod
    def render(self) -> None
    
    def run(self) -> None
        """Main event loop"""
```

### 5. Push2Adapter (Concrete Implementation)
**Location**: `adapters/push2_adapter.py`

Current UI logic refactored as adapter:
```python
class Push2Adapter(UIAdapter):
    def __init__(self, sequencer: SequencerEngine):
        super().__init__(sequencer)
        self.push = push2_python.Push2()
        self.ui_state = UIState()  # Local UI state only
    
    def handle_note_input(self, track: int, step: int, note: int) -> None:
        self.sequencer.add_note(track, step, note, 100)
    
    def on_sequencer_event(self, event: SequencerEvent) -> None:
        if event.type == "STEP_CHANGED":
            self._update_pad_colors()
        elif event.type == "PLAY_STATE_CHANGED":
            self._update_transport_buttons()
    
    def render(self) -> None:
        state = self.sequencer.get_state()
        frame = self._render_display(state)
        self.push.display.display_frame(frame)
```

### 6. Command Pattern (Optional but Recommended)
**Location**: `core/commands.py`

For advanced features like undo/redo and network transport:
```python
class Command(ABC):
    @abstractmethod
    def execute(self, sequencer: SequencerEngine) -> None
    @abstractmethod
    def undo(self, sequencer: SequencerEngine) -> None

class AddNoteCommand(Command):
    def __init__(self, track: int, step: int, note: int, velocity: int):
        self.track = track
        self.step = step
        self.note = note
        self.velocity = velocity
    
    def execute(self, sequencer: SequencerEngine) -> None:
        sequencer.add_note(self.track, self.step, self.note, self.velocity)
    
    def undo(self, sequencer: SequencerEngine) -> None:
        sequencer.remove_note(self.track, self.step)
```

## Data Flow (New Architecture)

### User Input → Sequencer → UI Update

```
Push2 Button Press
        ↓
Push2Adapter.handle_button_press()
        ↓
sequencer.play()  [Command execution]
        ↓
SequencerEngine updates state
        ↓
SequencerEventBus.publish(PlayStateChanged)
        ↓
Push2Adapter.on_sequencer_event()
        ↓
Push2Adapter._update_transport_buttons()
        ↓
Push2 Display Update
```

### Sequencer Playback → UI Update

```
SequencerEngine._play_loop()
        ↓
Trigger step notes
        ↓
SequencerEventBus.publish(StepChanged)
        ↓
Push2Adapter.on_sequencer_event()
        ↓
Push2Adapter._update_pad_colors()
        ↓
Push2 Display Update
```

## Implementation Strategy

### Phase 1: Core Abstraction (Foundation)
1. Create `SequencerState` immutable data class
2. Create `SequencerEventBus` pub/sub system
3. Create `UIAdapter` abstract base class
4. Extract core sequencer logic into `SequencerEngine`

**Outcome**: Sequencer can be tested independently

### Phase 2: Push2 Adapter (Refactor Current UI)
1. Move all Push2-specific code into `Push2Adapter`
2. Replace direct sequencer calls with command methods
3. Subscribe to sequencer events instead of callbacks
4. Maintain current functionality

**Outcome**: Push2 UI works with new architecture

### Phase 3: Network Layer (Optional)
1. Implement command serialization (JSON/Protocol Buffers)
2. Create WebSocket server for remote UIs
3. Support multiple simultaneous connections
4. Implement command validation

**Outcome**: Web/iOS UIs can control sequencer remotely

### Phase 4: Example Implementations
1. Build simple web UI (Flask + HTML/CSS)
2. Build CLI interface for testing
3. Document adapter pattern
4. Create template for new adapters

**Outcome**: Clear examples for building new UIs

## Benefits

| Benefit | Impact |
|---------|--------|
| **Testability** | Test sequencer logic without Push2 hardware |
| **Reusability** | Use same sequencer with web, iOS, CLI, etc. |
| **Maintainability** | Clear separation of concerns |
| **Extensibility** | Add new UIs without modifying core |
| **Scalability** | Support multiple simultaneous UIs |
| **Portability** | Run sequencer on server, UI on client |

## Migration Path

### Step 1: Parallel Implementation
- Keep existing code working
- Build new architecture alongside
- Run both simultaneously during transition

### Step 2: Gradual Refactoring
- Move one handler at a time to new architecture
- Test each component independently
- Maintain backward compatibility

### Step 3: Full Migration
- Replace old `SequencerApp` with new architecture
- Remove old code
- Update documentation

## File Structure (Proposed)

```
python-push-interface/
├── core/
│   ├── __init__.py
│   ├── sequencer_engine.py      # Core logic
│   ├── sequencer_state.py       # Immutable state
│   ├── sequencer_event_bus.py   # Pub/sub
│   ├── commands.py              # Command pattern
│   └── models.py                # Data models (Pattern, Note, etc.)
├── adapters/
│   ├── __init__.py
│   ├── ui_adapter.py            # Abstract base
│   ├── push2_adapter.py         # Push2 implementation
│   ├── web_adapter.py           # Web implementation (future)
│   └── cli_adapter.py           # CLI implementation (future)
├── transport/
│   ├── __init__.py
│   ├── serializer.py            # Command/event serialization
│   ├── websocket_server.py      # WebSocket transport
│   └── ipc_server.py            # Local IPC transport
├── midi_output.py               # Unchanged
├── dynamic_device_manager.py    # Unchanged
├── project_manager.py           # Unchanged
├── main.py                      # Entry point (updated)
└── tests/
    ├── test_sequencer_engine.py
    ├── test_adapters.py
    └── test_integration.py
```

## Key Design Principles

1. **Separation of Concerns**: Sequencer logic ≠ UI logic
2. **Dependency Inversion**: UI depends on sequencer interface, not vice versa
3. **Event-Driven**: Loose coupling via pub/sub
4. **Immutable State**: Prevent accidental state mutations
5. **Command Pattern**: Enable undo/redo and network transport
6. **Adapter Pattern**: Support multiple UI implementations

## Questions for You

Before implementation, please clarify:

1. **Network Transport**: Do you want remote UI support (web/iOS) or just local adapters?
2. **Undo/Redo**: Is this a required feature?
3. **Multi-User**: Should multiple UIs control the same sequencer simultaneously?
4. **Backward Compatibility**: How important is maintaining the current API?
5. **Timeline**: What's your preferred implementation pace (all at once vs. phased)?

## Next Steps

1. Review this proposal and provide feedback
2. Clarify the questions above
3. Approve the architecture
4. Switch to Code mode for implementation
5. Start with Phase 1 (Core Abstraction)

