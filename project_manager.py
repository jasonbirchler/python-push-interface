import json
import os
from datetime import datetime
from core.sequencer_event_bus import SequencerEvent, EventType

class ProjectManager:
    def __init__(self, sequencer_app):
        self.app = sequencer_app
        self.projects_dir = os.path.expanduser("~/push2-sequencer-projects")
        self.current_project_file = None  # Track currently loaded project
        self._ensure_projects_dir()
        
    def _ensure_projects_dir(self):
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)
            
    def save_project(self, filename):
        """Save current project state to JSON file"""
        project_data = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "bpm": self.app.sequencer.bpm,
            "current_track": self.app.current_track,
            "tracks": []
        }
        
        # Save each track
        for i in range(8):
            track_data = {
                "index": i,
                "device": None,
                "notes": []
            }
            
            # Save device info if assigned
            if self.app.tracks[i] is not None:
                device = self.app.tracks[i]
                track_data["device"] = self.app.device_manager.to_dict(device)
            
            # Save notes for this track
            pattern = self.app.sequencer._internal_sequencer.tracks[i]
            for note in pattern.notes:
                track_data["notes"].append({
                    "step": note.step,
                    "note": note.note,
                    "velocity": note.velocity
                })
                
            project_data["tracks"].append(track_data)
        
        # Save to file
        filepath = os.path.join(self.projects_dir, f"{filename}.json")
        with open(filepath, 'w') as f:
            json.dump(project_data, f, indent=2)
        self.current_project_file = filename
        print(f"Project saved: {filepath}")
        
    def load_project(self, filename):
        """Load project from JSON file"""
        filepath = os.path.join(self.projects_dir, f"{filename}.json")
        if not os.path.exists(filepath):
            print(f"Project file not found: {filepath}")
            return False
            
        try:
            with open(filepath, 'r') as f:
                project_data = json.load(f)
                
            # Clear current project
            self._clear_current_project()
            
            # Load BPM
            self.app.sequencer.set_bpm(project_data.get("bpm", 120))
            
            # Load tracks
            for track_data in project_data["tracks"]:
                track_idx = track_data["index"]
                
                # Load device if assigned
                if track_data["device"]:
                    device_info = track_data["device"]
                    # Recreate device from saved data
                    device = self.app.device_manager.from_dict(device_info)
                    if device and self.app.midi_output.connect(device.port):
                        self.app.tracks[track_idx] = device
                        self.app.sequencer.set_track_channel(track_idx, device.channel)
                        self.app.sequencer.set_track_port(track_idx, device.port)
                        self.app.sequencer.set_track_device(track_idx, device)
                
                # Load notes
                for note_data in track_data["notes"]:
                    self.app.sequencer._internal_sequencer.tracks[track_idx].add_note(
                        note_data["step"],
                        note_data["note"],
                        note_data["velocity"]
                    )
            
            # Set current track
            self.app.current_track = project_data.get("current_track", 0)
            
            # Update UI
            self.app._update_track_buttons()
            self.app._init_cc_values_for_track()
            self.app.event_bus.publish(SequencerEvent(
                type=EventType.PATTERN_MODIFIED,
                data={'action': 'project_loaded'}
            ))
            
            self.current_project_file = filename
            print(f"Project loaded: {filepath}")
            return True
            
        except Exception as e:
            print(f"Error loading project: {e}")
            return False
            
    def _clear_current_project(self):
        """Clear current project state"""
        # Stop sequencer
        self.app.sequencer.stop()
        
        # Clear all tracks
        for i in range(8):
            self.app.tracks[i] = None
            self.app.sequencer._internal_sequencer.tracks[i].notes.clear()
            
        # Reset to defaults
        self.app.current_track = 0
        self.app.sequencer.set_bpm(120)
        self.current_project_file = None
        

        
    def list_projects(self):
        """List available project files"""
        if not os.path.exists(self.projects_dir):
            return []
        files = [f[:-5] for f in os.listdir(self.projects_dir) if f.endswith('.json')]
        return sorted(files)
