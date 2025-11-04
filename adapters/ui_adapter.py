from abc import ABC, abstractmethod
from core.sequencer_engine import SequencerEngine
from core.sequencer_event_bus import SequencerEvent

class UIAdapter(ABC):
    """Abstract base class for all UI implementations"""
    
    def __init__(self, sequencer: SequencerEngine):
        self.sequencer = sequencer
        self.event_bus = sequencer.event_bus
    
    @abstractmethod
    def run(self) -> None:
        """Start the UI event loop"""
        pass
    
    @abstractmethod
    def on_sequencer_event(self, event: SequencerEvent) -> None:
        """Handle sequencer events"""
        pass
    
    def shutdown(self) -> None:
        """Cleanup resources"""
        pass