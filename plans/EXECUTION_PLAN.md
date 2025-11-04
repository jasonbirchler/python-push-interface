# Execution Plan: Sequencer Decoupling

## Overview

Based on your requirements:
- ✅ **No network support needed** - Focus on Push2 only
- ✅ **No backward compatibility required** - Clean break allowed
- ✅ **Feature parity required** - No regressions during migration
- ✅ **No specific deadlines** - Quality over speed

This plan focuses on **3 core phases** to decouple the sequencer from the Push2 UI.

---

## Phase 1: Core Abstraction (Foundation)

### Objective
Create the core sequencer logic with no UI dependencies, making it independently testable.

### Files to Create

#### 1. `core/__init__.py`
```python
"""Core sequencer components"""
from .sequencer_state import SequencerState
from .sequencer_event_bus import SequencerEventBus, SequencerEvent, EventType
from .sequencer_engine import SequencerEngine

__all__ = ['SequencerState', 'SequencerEventBus', 'SequencerEvent', 'EventType', 'SequencerEngine']
```

#### 2. `core/sequencer_state.py`
Immutable snapshot of sequencer state (see IMPLEMENTATION_GUIDE.md for full code)

#### 3. `core/sequencer_event_bus.py`
Pub/sub event system (see IMPLEMENTATION_GUIDE.md for full code)

#### 4. `core/sequencer_engine.py`
Core sequencer logic refactored from `sequencer.py` (see IMPLEMENTATION_GUIDE.md for full code)

#### 5. `adapters/__init__.py`
```python
"""UI adapter implementations"""
from .ui_adapter import UIAdapter

__all__ = ['UIAdapter']
```

#### 6. `adapters/ui_adapter.py`
Abstract base class for all UIs (see IMPLEMENTATION_GUIDE.md for full code)

### Testing Phase 1

Create `tests/test_core_abstraction.py`:
```python
import pytest
from core.sequencer_engine import SequencerEngine
from core.sequencer_event_bus import EventType
from midi_output import MidiOutput

def test_sequencer_engine_creation():
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    assert engine.bpm == 120
    assert engine.is_playing == False
    assert engine.current_step == 0

def test_sequencer_state_snapshot():
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    state = engine.get_state()
    assert state.bpm == 120
    assert state.is_playing == False

def test_event_bus_subscription():
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    
    events_received = []
    def on_event(event):
        events_received.append(event)
    
    engine.event_bus.subscribe(EventType.BPM_CHANGED, on_event)
    engine.set_bpm(140)
    
    assert len(events_received) == 1
    assert events_received[0].data['bpm'] == 140

def test_add_note():
    midi_output = MidiOutput()
    engine = SequencerEngine(midi_output)
    
    engine.add_note(0, 0, 60, 100)
    notes = engine.get_track_notes(0)
    assert len(notes) == 1
    assert notes[0].note == 60
```

### Phase 1 Checklist
- [ ] Create `core/` directory with all files
- [ ] Create `adapters/` directory with base class
- [ ] All unit tests pass
- [ ] Sequencer can be instantiated and used without Push2
- [ ] Events are published correctly
- [ ] State snapshots work as expected

### Phase 1 Outcome
✅ Sequencer core is testable independently  
✅ Event system is working  
✅ Foundation for adapters is in place  

---

## Phase 2: Push2Adapter (Refactor Current UI)

### Objective
Move all Push2-specific code into an adapter that implements the UIAdapter interface, maintaining feature parity.

### Files to Create

#### 1. `adapters/push2_adapter.py`
Refactored Push2 UI code (see detailed implementation below)

### Implementation Strategy

The Push2Adapter should:
1. Implement all abstract methods from UIAdapter
2. Subscribe to sequencer events
3. Handle Push2 input (buttons, pads, encoders)
4. Update Push2 display based on events
5. Maintain all current features

### Key Methods to Implement

```python
class Push2Adapter(UIAdapter):
    def __init__(self, sequencer_engine):
        super().__init__(sequencer_engine)
        self.push = push2_python.Push2()
        self.ui_state = UIState()  # Local UI state only
        self._setup_handlers()
    
    # Commands (UI → Sequencer)
    def handle_play(self) -> None
    def handle_stop(self) -> None
    def handle_note_input(self, track, step, note, velocity) -> None
    def handle_note_delete(self, track, step) -> None
    def handle_set_bpm(self, bpm) -> None
    def handle_set_track(self, track) -> None
    
    # Event Handlers (Sequencer → UI)
    def on_sequencer_event(self, event) -> None
    def render(self) -> None
    
    # Lifecycle
    def run(self) -> None
    def shutdown(self) -> None
```

### Feature Parity Checklist

Ensure all current features work:
- [ ] Play/Stop buttons
- [ ] Track selection (Lower Row buttons)
- [ ] Note input (Top row pads)
- [ ] Step sequencer (Bottom 2 rows)
- [ ] Octave up/down
- [ ] Delete button
- [ ] Mute/Solo
- [ ] Device selection
- [ ] Clock source selection
- [ ] Session management (save/load)
- [ ] Encoder CC control
- [ ] Display rendering
- [ ] All visual feedback

### Phase 2 Checklist
- [ ] Create `adapters/push2_adapter.py`
- [ ] All button handlers working
- [ ] All pad handlers working
- [ ] All encoder handlers working
- [ ] Display updates correctly
- [ ] All features from original working
- [ ] No feature regressions
- [ ] Integration tests pass

### Phase 2 Outcome
✅ Push2 UI works with new architecture  
✅ All features maintained  
✅ No regressions  

---

## Phase 3: Cleanup & Integration

### Objective
Remove old code and integrate new architecture into main entry point.

### Files to Modify

#### 1. `main.py`
Update to use new architecture:
```python
from core.sequencer_engine import SequencerEngine
from adapters.push2_adapter import Push2Adapter
from midi_output import MidiOutput
import sys

if __name__ == "__main__":
    use_simulator = '--simulator' in sys.argv or '-s' in sys.argv
    
    # Create core components
    midi_output = MidiOutput()
    sequencer = SequencerEngine(midi_output)
    midi_output.set_sequencer(sequencer)  # For clock sync
    
    # Create UI adapter
    ui = Push2Adapter(sequencer)
    
    # Run
    ui.run()
```

#### 2. `sequencer_app.py`
**Delete or archive** - functionality moved to Push2Adapter

#### 3. Update imports in handlers
Remove references to old SequencerApp, use adapter pattern instead

### Files to Review for Cleanup
- [ ] `sequencer.py` - Keep or archive?
- [ ] `ui_main.py` - Functionality moved to adapter
- [ ] `handlers/` - Refactored into adapter
- [ ] `ui/` - Functionality moved to adapter

### Phase 3 Checklist
- [ ] Update `main.py` to use new architecture
- [ ] Remove old `sequencer_app.py`
- [ ] Remove old UI code
- [ ] Update all imports
- [ ] Full integration test passes
- [ ] No feature regressions
- [ ] Codebase is clean

### Phase 3 Outcome
✅ Clean, organized codebase  
✅ New architecture in place  
✅ All features working  

---

## Phase 4: Documentation & Polish

### Objective
Document the new architecture and ensure maintainability.

### Files to Create/Update

#### 1. Update `README.md`
- Explain new architecture
- Document how to use SequencerEngine
- Document how to create new adapters
- Update setup/run instructions

#### 2. Create `ARCHITECTURE.md`
- Overview of new architecture
- Component descriptions
- Event types and data flows
- How to extend with new adapters

#### 3. Add docstrings
- Document all public methods
- Add type hints
- Add usage examples

### Phase 4 Checklist
- [ ] README updated
- [ ] Architecture documented
- [ ] All public methods have docstrings
- [ ] Code is well-commented
- [ ] Examples provided for extending

### Phase 4 Outcome
✅ Well-documented codebase  
✅ Easy to maintain and extend  
✅ Clear for future developers  

---

## Testing Strategy

### Unit Tests (Phase 1)
Test core components in isolation:
- SequencerEngine creation and state
- SequencerEventBus pub/sub
- Event publishing and subscription
- State snapshots

### Integration Tests (Phase 2)
Test adapter with sequencer:
- Button presses trigger sequencer commands
- Sequencer events update UI
- Feature parity with original

### End-to-End Tests (Phase 3)
Test full system:
- Play/stop functionality
- Note input and playback
- All UI features
- No regressions

### Test Files
- `tests/test_core_abstraction.py` - Phase 1 tests
- `tests/test_push2_adapter.py` - Phase 2 tests
- `tests/test_integration.py` - Phase 3 tests

---

## Risk Mitigation

### Feature Regression Prevention
1. **Test each feature** as it's migrated
2. **Compare behavior** with original implementation
3. **Run full test suite** before moving to next phase
4. **Keep original code** available for reference during migration

### Testing Approach
1. Create comprehensive tests for each feature
2. Run tests after each component is migrated
3. Use simulator mode for testing without hardware
4. Document any behavior differences

### Rollback Plan
If issues arise:
1. Keep old code in separate branch
2. Can revert to old implementation if needed
3. Identify specific issues and fix in new architecture

---

## Implementation Order

### Phase 1 (Foundation)
1. Create `core/sequencer_state.py`
2. Create `core/sequencer_event_bus.py`
3. Create `core/sequencer_engine.py`
4. Create `adapters/ui_adapter.py`
5. Write and run unit tests
6. Verify sequencer works independently

### Phase 2 (Push2 Adapter)
1. Create `adapters/push2_adapter.py` skeleton
2. Implement button handling
3. Implement pad handling
4. Implement encoder handling
5. Implement display rendering
6. Test each feature
7. Verify feature parity

### Phase 3 (Cleanup)
1. Update `main.py`
2. Remove old code
3. Update imports
4. Run full integration tests
5. Verify no regressions

### Phase 4 (Documentation)
1. Update README
2. Create ARCHITECTURE.md
3. Add docstrings
4. Add comments

---

## Success Criteria

### Phase 1 Complete
✅ Sequencer can be instantiated without Push2  
✅ Events are published and received correctly  
✅ State snapshots work  
✅ Unit tests pass  

### Phase 2 Complete
✅ All Push2 features work  
✅ No feature regressions  
✅ Integration tests pass  
✅ UI is responsive  

### Phase 3 Complete
✅ New architecture is primary  
✅ Old code is removed  
✅ Codebase is clean  
✅ All tests pass  

### Phase 4 Complete
✅ Architecture is documented  
✅ Code is well-commented  
✅ Easy to extend  
✅ Ready for future development  

---

## Timeline Estimate

| Phase | Tasks | Estimate |
|-------|-------|----------|
| 1 | Core abstraction | 2-3 hours |
| 2 | Push2 adapter | 3-4 hours |
| 3 | Cleanup | 1-2 hours |
| 4 | Documentation | 1-2 hours |
| **Total** | **All phases** | **7-11 hours** |

---

## Key Files Reference

### New Files to Create
```
core/
├── __init__.py
├── sequencer_state.py
├── sequencer_event_bus.py
└── sequencer_engine.py

adapters/
├── __init__.py
├── ui_adapter.py
└── push2_adapter.py

tests/
├── test_core_abstraction.py
├── test_push2_adapter.py
└── test_integration.py
```

### Files to Modify
- `main.py` - Update entry point
- `README.md` - Update documentation

### Files to Remove/Archive
- `sequencer_app.py` - Functionality moved to adapter
- `ui_main.py` - Functionality moved to adapter
- `handlers/` - Functionality moved to adapter
- `ui/` - Functionality moved to adapter

---

## Next Steps

1. **Review this plan** - Confirm approach
2. **Switch to Code mode** - Begin Phase 1
3. **Implement Phase 1** - Create core components
4. **Test Phase 1** - Verify sequencer works independently
5. **Implement Phase 2** - Create Push2Adapter
6. **Test Phase 2** - Verify feature parity
7. **Implement Phase 3** - Cleanup and integration
8. **Implement Phase 4** - Documentation

---

## Notes

- All code examples are in `IMPLEMENTATION_GUIDE.md`
- Architecture details are in `ARCHITECTURE_PROPOSAL.md`
- Visual diagrams are in `ARCHITECTURE_DIAGRAMS.md`
- This plan focuses on Push2 only (no network layer)
- Feature parity is maintained throughout migration
- No backward compatibility required

