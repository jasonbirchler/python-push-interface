import json
import mido
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class MidiDevice:
    name: str
    port: str
    channel: int = 1
    send_transport: bool = True
    cc_mappings: Dict[str, int] = None
    
    def __post_init__(self):
        if self.cc_mappings is None:
            self.cc_mappings = {}

class DynamicDeviceManager:
    def __init__(self, cc_library_file="devices.json"):
        self.cc_library_file = cc_library_file
        self.cc_library = {}
        self.available_ports = []
        self.current_devices = []
        self._load_cc_library()
        self._scan_available_ports()
        
    def _load_cc_library(self):
        """Load CC mappings library from JSON file"""
        try:
            with open(self.cc_library_file, 'r') as f:
                data = json.load(f)
                for device in data.get("devices", []):
                    self.cc_library[device["name"]] = {
                        "cc_mappings": device.get("cc_mappings", {}),
                        "send_transport": device.get("send_transport", True)
                    }
            print(f"Loaded CC library with {len(self.cc_library)} device profiles")
        except Exception as e:
            print(f"Warning: Could not load CC library: {e}")
            self.cc_library = {}
            
    def _scan_available_ports(self):
        """Scan all available MIDI output ports"""
        try:
            self.available_ports = mido.get_output_names()
            # Add virtual port to available ports list
            self.available_ports.append("Push Sequencer Out")
            
            # Create device entries for all available ports
            self.current_devices = []
            for port in self.available_ports:
                # Try to match with CC library
                cc_mappings = {}
                send_transport = True
                
                # Look for exact match or partial match in CC library
                for lib_name, lib_data in self.cc_library.items():
                    if lib_name.lower() in port.lower() or port.lower() in lib_name.lower():
                        cc_mappings = lib_data["cc_mappings"]
                        send_transport = lib_data["send_transport"]
                        break
                
                device = MidiDevice(
                    name=port,
                    port=port,
                    channel=1,
                    send_transport=send_transport,
                    cc_mappings=cc_mappings
                )
                self.current_devices.append(device)
                
            print(f"Found {len(self.current_devices)} available MIDI devices")
        except Exception as e:
            print(f"Error scanning MIDI ports: {e}")
            self.current_devices = []
            
    def refresh_devices(self):
        """Refresh the list of available devices"""
        self._scan_available_ports()
        
    def get_device_count(self):
        return len(self.current_devices)
        
    def get_device_by_index(self, index):
        if 0 <= index < len(self.current_devices):
            return self.current_devices[index]
        return None
        
    def get_device_by_name(self, name):
        """Find device by name"""
        for device in self.current_devices:
            if device.name == name:
                return device
        return None
        
    def create_custom_device(self, name, port, channel=1, send_transport=True):
        """Create a custom device configuration"""
        # Check if port exists
        if port not in self.available_ports:
            return None
            
        # Look for CC mappings in library
        cc_mappings = {}
        for lib_name, lib_data in self.cc_library.items():
            if lib_name.lower() in name.lower() or name.lower() in lib_name.lower():
                cc_mappings = lib_data["cc_mappings"]
                break
                
        return MidiDevice(
            name=name,
            port=port,
            channel=channel,
            send_transport=send_transport,
            cc_mappings=cc_mappings
        )
        
    def get_available_ports(self):
        """Get list of available MIDI port names"""
        return self.available_ports.copy()
        
    def to_dict(self, device):
        """Convert device to dictionary for project saving"""
        return {
            "name": device.name,
            "port": device.port,
            "channel": device.channel,
            "send_transport": device.send_transport,
            "cc_mappings": device.cc_mappings
        }
        
    def from_dict(self, device_dict):
        """Create device from dictionary for project loading"""
        return MidiDevice(
            name=device_dict["name"],
            port=device_dict["port"],
            channel=device_dict.get("channel", 1),
            send_transport=device_dict.get("send_transport", True),
            cc_mappings=device_dict.get("cc_mappings", {})
        )
