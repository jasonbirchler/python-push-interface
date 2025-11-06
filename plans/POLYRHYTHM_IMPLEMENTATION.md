# Polyrhythmic Sequencer Implementation Plan

## Overview

Extend the sequencer to support individual track pattern lengths (1-64 steps) while maintaining synchronized timing, enabling polyrhythmic compositions.

## Core Changes Required

### 1. Pattern Class Modifications (`sequencer.py`)

```python
class Pattern:
    def __init__(self, length: int = 16):
        self.length = max(1, min(64, length))  # Clamp to 1-64
        self.notes: List[Note] = []
        self.current_step = 0  # Track-specific step counter
        
    def add_note(self, step: int, note: int, velocity: int = 100):
        if step < self.length:  # Only within pattern length
            # Remove existing note at this step if any
            self.notes = [n for n in self.notes if n.step != step]
            # Add new note
            self.notes.append(Note(step, note, velocity))
```

### 2. Sequencer Class Changes

```python
class Sequencer:
    def __init__(self, midi_output, bpm: int = 120):
        # Replace single current_step with array
        self.current_steps = [0] * 8  # Individual step counter per track
        
    def _trigger_step(self):
        # Advance each track independently based on global timing
        for track_idx, track_pattern in enumerate(self.tracks):
            # Check if track should be audible
            if hasattr(self, 'app_ref') and self.app_ref and not self.app_ref._is_track_audible(track_idx):
                continue
                
            # Use track's own step counter
            current_track_step = self.current_steps[track_idx]
            notes_at_step = track_pattern.get_notes_at_step(current_track_step)
            
            # Play notes...
            
            # Advance this track's step counter independently
            self.current_steps[track_idx] = (current_track_step + 1) % track_pattern.length
```

### 3. Sequencer Engine Interface Updates (`core/sequencer_engine.py`)

```python
def set_pattern_length(self, track: int, length: int) -> None:
    """Set pattern length for specific track"""
    if 0 <= track < len(self._internal_sequencer.tracks):
        old_length = self._internal_sequencer.tracks[track].length
        self._internal_sequencer.tracks[track].length = max(1, min(64, length))
        
        # Publish event for UI updates
        self.event_bus.publish(SequencerEvent(
            type=EventType.PATTERN_LENGTH_CHANGED,
            data={'track': track, 'length': length, 'old_length': old_length}
        ))

def get_pattern_length(self, track: int) -> int:
    """Get pattern length for specific track"""
    if 0 <= track < len(self._internal_sequencer.tracks):
        return self._internal_sequencer.tracks[track].length
    return 16  # Default

@property
def track_steps(self) -> List[int]:
    """Get current step for each track"""
    return self._internal_sequencer.current_steps.copy()
```

## Push UI Integration

### 4. Display Updates (`adapters/push2_adapter.py`)

```python
def _update_pad_colors(self):
    """Update pad colors for variable-length patterns"""
    # Clear all step sequencer pads
    for row in range(6, 8):
        for col in range(8):
            self.push.pads.set_pad_color((row, col), 'black')
    
    # Get current pattern length for active track
    active_pattern_length = self.sequencer.get_pattern_length(self.current_track)
    
    # Only show active steps up to pattern length
    for step in range(min(16, active_pattern_length)):
        row = 6 + (step // 8)
        col = step % 8
        
        # Check if this step is current for the active track
        track_steps = self.sequencer.track_steps
        is_current_step = (track_steps[self.current_track] == step and 
                          self.sequencer.is_playing)
        
        if is_current_step:
            color = 'green'
        elif self.sequencer._internal_sequencer.tracks[self.current_track].get_notes_at_step(step):
            color = self.track_colors[self.current_track]
        else:
            color = 'white'
            
        self.push.pads.set_pad_color((row, col), color)
    
    # Show inactive steps in gray
    for step in range(active_pattern_length, 16):
        row = 6 + (step // 8)
        col = step % 8
        self.push.pads.set_pad_color((row, col), 'dark_gray')
```

### 5. Length Control Interface

```python
def handle_length_adjustment(self, track: int, increment: int):
    """Adjust pattern length for track using encoder"""
    current_length = self.sequencer.get_pattern_length(track)
    new_length = max(1, min(64, current_length + increment))
    
    if new_length != current_length:
        self.sequencer.set_pattern_length(track, new_length)
        print(f"Track {track} length: {current_length} -> {new_length}")
        
        # Update display to show new active range
        self._update_pad_colors()

# Integration with existing encoder handling
def _setup_length_control_handlers(self):
    """Map encoders 1-8 to pattern length control for tracks 1-8"""
    for encoder_idx in range(8):
        @push2_python.on_encoder_rotated()
        def on_encoder_rotated(encoder_name, increment):
            if encoder_name == f'ENCODER_{encoder_idx + 1}':
                self.handle_length_adjustment(encoder_idx, increment)
```

## Display Information

### 6. Pattern Length Display

```python
def get_length_display_frame(self):
    """Create display frame showing pattern lengths"""
    frame = self.ui.get_current_frame()
    
    # Show pattern lengths for all tracks
    for track in range(8):
        length = self.sequencer.get_pattern_length(track)
        current_step = self.sequencer.track_steps[track]
        
        # Display: "T1:16" format
        text = f"T{track+1}:{length}"
        if track == self.current_track:
            text += "*"  # Mark active track
            
        # Position text on screen
        x_pos = track * 20
        frame.draw_text(x_pos, 0, text, color='white' if track == self.current_track else 'gray')
    
    return frame
```

## Polyrhythmic Behavior Examples

### Example Setup

- Track 1: 16 steps (standard 4/4)
- Track 2: 12 steps (3/4 feel)  
- Track 3: 8 steps (2/4 feel)
- Track 4: 9 steps (interesting polyrhythm)

### Timing Behavior

- All tracks advance simultaneously on each 16th note
- Track 1 loops every 16 steps (4 bars)
- Track 2 loops every 12 steps (3 bars)
- Track 3 loops every 8 steps (2 bars)  
- Track 4 loops every 9 steps (irregular)
- Creates complex polyrhythmic relationships

## Testing Strategy

### 7. Test Coverage

```python
def test_polyrhythmic_independent_progression():
    """Test that tracks advance independently"""
    # Setup tracks with different lengths
    sequencer.set_pattern_length(0, 8)   # 8-step track
    sequencer.set_pattern_length(1, 12)  # 12-step track
    
    # Advance global step 16 times
    for _ in range(16):
        sequencer._trigger_step()
    
    # Track 0 should loop twice (16/8 = 2)
    assert sequencer.track_steps[0] == 0
    
    # Track 1 should loop once and advance 4 steps (16-12 = 4)  
    assert sequencer.track_steps[1] == 4

def test_pattern_length_bounds():
    """Test pattern length constraints"""
    sequencer.set_pattern_length(0, 0)    # Should clamp to 1
    assert sequencer.get_pattern_length(0) == 1
    
    sequencer.set_pattern_length(0, 100)  # Should clamp to 64
    assert sequencer.get_pattern_length(0) == 64

def test_notes_outside_pattern_length():
    """Test that notes beyond pattern length are handled"""
    sequencer.set_pattern_length(0, 4)
    
    # Should only add note if within pattern length
    sequencer.tracks[0].add_note(2, 60)  # Within length - should work
    sequencer.tracks[0].add_note(10, 62) # Beyond length - should be ignored
```

## Integration Points

### Event System Updates

- Add `PATTERN_LENGTH_CHANGED` event type
- Update UI on pattern length changes
- Preserve existing pattern modification events

### MIDI Clock Synchronization

- External sync continues to work with polyrhythms
- Each track maintains independent step position during external sync
- Global timing remains consistent

### Project Persistence

- Save/load pattern lengths with project data
- Maintain compatibility with existing 16-step projects
- Migrate existing projects to new format automatically

## Migration Strategy

### Backward Compatibility

- Default all new patterns to 16 steps (existing behavior)
- Only enable polyrhythmic features when lengths differ
- Smooth transition for existing projects

This implementation maintains the current timing accuracy while enabling rich polyrhythmic compositions through independent track loop lengths.
