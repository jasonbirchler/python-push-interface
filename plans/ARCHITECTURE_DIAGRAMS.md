# Architecture Diagrams

## 1. Current Architecture (Tightly Coupled)

```
┌─────────────────────────────────────────────────────────────┐
│                     SequencerApp                            │
│  (Monolithic - mixes sequencer, UI state, and Push2)       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Sequencer Logic                                      │  │
│  │ - Pattern/track management                           │  │
│  │ - MIDI playback                                      │  │
│  │ - Callbacks to UI (_update_pad_colors_callback)      │  │
│  │ - App references (self.app_ref)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ UI State Management                                  │  │
│  │ - Track assignments                                  │  │
│  │ - Device selection mode                              │  │
│  │ - Mute/solo state                                    │  │
│  │ - Pad colors                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Push2 Handling                                       │  │
│  │ - Button handlers                                    │  │
│  │ - Pad handlers                                       │  │
│  │ - Encoder handlers                                   │  │
│  │ - Display rendering                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ MIDI Output                                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Problems:**
- Cannot test sequencer without Push2
- Cannot use sequencer with different UI
- Difficult to add new features
- Hard to debug issues

---

## 2. Proposed Architecture (Decoupled)

```
┌──────────────────────────────────────────────────────────────────┐
│                      SEQUENCER CORE                              │
│              (Pure business logic, no UI deps)                   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ SequencerEngine                                            │ │
│  │ - Pattern/track management                                │ │
│  │ - MIDI playback logic                                     │ │
│  │ - State queries (getters only)                            │ │
│  │ - Command execution                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ SequencerState (Immutable)                                │ │
│  │ - is_playing, current_step, bpm                           │ │
│  │ - tracks, track_channels, current_track                   │ │
│  │ - Read-only snapshots                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ SequencerEventBus (Pub/Sub)                               │ │
│  │ - StepChanged, NoteTriggered, PlayStateChanged            │ │
│  │ - BpmChanged, TrackChanged, PatternModified               │ │
│  │ - Subscribers notified of all state changes               │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Push2Adapter    │  │  WebAdapter      │  │  CLIAdapter      │
│  (UI Layer)      │  │  (UI Layer)      │  │  (UI Layer)      │
│                  │  │                  │  │                  │
│ - Button handler │  │ - HTTP handler   │  │ - Input parser   │
│ - Pad renderer   │  │ - WebSocket      │  │ - Text output    │
│ - Display update │  │ - React state    │  │ - Simple display │
│ - Encoder input  │  │ - REST API       │  │ - Testing        │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        ↓                     ↓                     ↓
    Push2 Device        Web Browser          Terminal/Tests
```

**Benefits:**
- Sequencer is testable independently
- Multiple UIs can use same sequencer
- Easy to add new UI implementations
- Clear separation of concerns

---

## 3. Event Flow Diagram

### User Input → Sequencer → UI Update

```
┌─────────────────────────────────────────────────────────────┐
│ Push2 Button Press (e.g., Play button)                      │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Push2Adapter.handle_button_press(BUTTON_PLAY)               │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ sequencer.play()  [Command execution]                       │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ SequencerEngine updates internal state                       │
│ - Sets is_playing = True                                    │
│ - Starts playback thread                                    │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ SequencerEventBus.publish(PlayStateChanged)                 │
│ - event.is_playing = True                                   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ All subscribers notified:                                   │
│ - Push2Adapter.on_sequencer_event(event)                    │
│ - WebAdapter.on_sequencer_event(event)                      │
│ - CLIAdapter.on_sequencer_event(event)                      │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Push2Adapter._update_transport_buttons()                    │
│ - Sets Play button to green                                 │
│ - Sets Stop button to white                                 │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Push2 Display Update                                        │
│ - User sees visual feedback                                 │
└─────────────────────────────────────────────────────────────┘
```

### Sequencer Playback → UI Update

```
┌─────────────────────────────────────────────────────────────┐
│ SequencerEngine._play_loop() running                        │
│ - Timing thread checks if step should advance               │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step time reached                                           │
│ - current_step advances (0 → 1 → 2 ... → 15 → 0)           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ SequencerEngine._trigger_step()                             │
│ - Gets notes at current step                                │
│ - Sends MIDI note-on messages                               │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ SequencerEventBus.publish(StepChanged)                      │
│ - event.current_step = 5                                    │
│ - event.notes_triggered = [Note(60), Note(64)]              │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ All subscribers notified:                                   │
│ - Push2Adapter.on_sequencer_event(event)                    │
│ - WebAdapter.on_sequencer_event(event)                      │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Push2Adapter._update_pad_colors()                           │
│ - Sets step 5 pad to green (current step)                   │
│ - Sets step 4 pad back to orange (previous step)            │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Push2 Display Update                                        │
│ - User sees step indicator moving                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Class Hierarchy

```
UIAdapter (Abstract Base Class)
├── Push2Adapter
│   ├── Handles Push2 input (buttons, pads, encoders)
│   ├── Renders to Push2 display
│   └── Manages Push2-specific state
├── WebAdapter
│   ├── Handles HTTP/WebSocket input
│   ├── Renders JSON state
│   └── Manages web session state
└── CLIAdapter
    ├── Handles stdin input
    ├── Renders to stdout
    └── Manages CLI session state
```

---

## 5. State Management Flow

```
┌──────────────────────────────────────────────────────────┐
│ SequencerEngine (Mutable internal state)                 │
│ - Tracks list                                            │
│ - Current step counter                                   │
│ - BPM value                                              │
│ - Playing flag                                           │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ get_state() called
                 ↓
┌──────────────────────────────────────────────────────────┐
│ SequencerState (Immutable snapshot)                      │
│ - Frozen dataclass                                       │
│ - Safe to pass to UIs                                    │
│ - Cannot be modified                                     │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ Distributed to all adapters
                 ├─────────────────┬──────────────────┐
                 ↓                 ↓                  ↓
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ Push2Adapter │  │ WebAdapter   │  │ CLIAdapter   │
        │ Local state  │  │ Local state  │  │ Local state  │
        └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 6. Command Pattern (Optional)

```
┌─────────────────────────────────────────────────────────┐
│ Command (Abstract)                                      │
│ - execute(sequencer)                                    │
│ - undo(sequencer)                                       │
│ - serialize()                                           │
└─────────────────────────────────────────────────────────┘
        ↑
        │ Implements
        ├─────────────────────────────────────────────────┐
        │                                                 │
┌───────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ AddNoteCommand    │  │ RemoveNoteCommand│  │ SetBpmCommand    │
│ - track, step     │  │ - track, step    │  │ - bpm            │
│ - note, velocity  │  │ - note           │  │                  │
└───────────────────┘  └──────────────────┘  └──────────────────┘

Benefits:
- Undo/redo support
- Network transport (serialize commands)
- Command history/logging
- Macro recording
```

---

## 7. Network Architecture (Future)

```
┌──────────────────────────────────────────────────────────┐
│ SequencerEngine (Server)                                 │
│ - Runs on Raspberry Pi                                   │
│ - Manages all sequencer state                            │
│ - Publishes events                                       │
└────────────────┬─────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ↓            ↓            ↓
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Push2   │  │ Web UI  │  │ iOS App │
│ (USB)   │  │ (WiFi)  │  │ (WiFi)  │
└─────────┘  └─────────┘  └─────────┘
    │            │            │
    └────────────┼────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ↓                 ↓
    Commands          Events
    (JSON)            (JSON)
    
    ↓                 ↑
    
    WebSocket Server / REST API
    (on Raspberry Pi)
```

---

## 8. Testing Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Unit Tests                                               │
│ - Test SequencerEngine in isolation                      │
│ - Mock MidiOutput                                        │
│ - No UI dependencies                                     │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ Adapter Tests                                            │
│ - Test each adapter independently                        │
│ - Mock SequencerEngine                                   │
│ - Verify event handling                                  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ Integration Tests                                        │
│ - Test SequencerEngine + Adapter together                │
│ - Verify event flow                                      │
│ - Test state synchronization                             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ End-to-End Tests                                         │
│ - Test full system with real hardware (optional)         │
│ - Verify MIDI output                                     │
│ - Test UI responsiveness                                 │
└──────────────────────────────────────────────────────────┘
```

