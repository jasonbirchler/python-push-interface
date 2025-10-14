import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Device:
    name: str
    channel: int
    port: str
    cc_mappings: Dict[str, int]

class DeviceManager:
    def __init__(self, config_file: str = "devices.json"):
        self.config_file = config_file
        self.devices: List[Device] = []
        self.current_device_index = 0
        self.load_devices()

    def load_devices(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.devices = [
                        Device(
                            name=d['name'],
                            channel=d['channel'],
                            port=d['port'],
                            cc_mappings=d.get('cc_mappings', {})
                        )
                        for d in data['devices']
                    ]
            except Exception as e:
                print(f"Error loading devices: {e}")
                self._create_default_devices()
        else:
            self._create_default_devices()

    def _create_default_devices(self):
        self.devices = [
            Device(
                name="PlinkySynth",
                channel=1,
                port="PlinkySynth MIDI",
                cc_mappings={
                    "Filter Cutoff": 74,
                    "Filter Resonance": 71,
                    "Envelope Attack": 73,
                    "Envelope Decay": 75
                }
            ),
            Device(
                name="Drum Machine",
                channel=10,
                port="UltraLite-mk4-L MIDI Out",
                cc_mappings={
                    "Volume": 7,
                    "Pan": 10
                }
            )
        ]
        self.save_devices()

    def save_devices(self):
        data = {
            "devices": [
                {
                    "name": device.name,
                    "channel": device.channel,
                    "port": device.port,
                    "cc_mappings": device.cc_mappings
                }
                for device in self.devices
            ]
        }
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_current_device(self) -> Optional[Device]:
        if self.devices and 0 <= self.current_device_index < len(self.devices):
            return self.devices[self.current_device_index]
        return None

    def next_device(self):
        if self.devices:
            self.current_device_index = (self.current_device_index + 1) % len(self.devices)

    def prev_device(self):
        if self.devices:
            self.current_device_index = (self.current_device_index - 1) % len(self.devices)

    def get_device_count(self) -> int:
        return len(self.devices)

    def get_device_by_index(self, index: int) -> Optional[Device]:
        if 0 <= index < len(self.devices):
            return self.devices[index]
        return None
