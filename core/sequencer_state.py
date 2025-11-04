from dataclasses import dataclass
from typing import List, Tuple, Optional
from sequencer import Pattern, Note

@dataclass(frozen=True)
class SequencerState:
    """Immutable snapshot of sequencer state"""
    is_playing: bool
    current_step: int
    bpm: int
    tracks: Tuple[Optional[Pattern], ...]
    current_track: int
    
    def get_notes_at_step(self, track: int, step: int) -> List[Note]:
        """Get notes at specific track and step"""
        if 0 <= track < len(self.tracks) and self.tracks[track] is not None:
            return self.tracks[track].get_notes_at_step(step)
        return []
    
    def get_track_pattern(self, track: int) -> Optional[Pattern]:
        """Get pattern for specific track"""
        if 0 <= track < len(self.tracks):
            return self.tracks[track]
        return None