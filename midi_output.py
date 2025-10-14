import mido
from typing import Optional

class MidiOutput:
    def __init__(self):
        self.output_port: Optional[mido.ports.BaseOutput] = None
        self.available_ports = []
        self._scan_ports()
        
    def _scan_ports(self):
        self.available_ports = mido.get_output_names()
        
    def connect(self, port_name: Optional[str] = None):
        if port_name is None and self.available_ports:
            port_name = self.available_ports[0]
            
        if port_name:
            try:
                self.output_port = mido.open_output(port_name)
                return True
            except Exception as e:
                print(f"Failed to connect to MIDI port {port_name}: {e}")
                return False
        return False
        
    def disconnect(self):
        if self.output_port:
            self.output_port.close()
            self.output_port = None
            
    def send_note_on(self, channel: int, note: int, velocity: int):
        if self.output_port:
            msg = mido.Message('note_on', channel=channel-1, note=note, velocity=velocity)
            self.output_port.send(msg)

            
    def send_note_off(self, channel: int, note: int):
        if self.output_port:
            msg = mido.Message('note_off', channel=channel-1, note=note, velocity=0)
            self.output_port.send(msg)
            
    def send_cc(self, channel: int, cc_number: int, value: int):
        if self.output_port:
            msg = mido.Message('control_change', channel=channel-1, control=cc_number, value=value)
            self.output_port.send(msg)

    def send_clock(self):
        if self.output_port:
            msg = mido.Message('clock')
            self.output_port.send(msg)

            
    def send_start(self):
        if self.output_port:
            msg = mido.Message('start')
            self.output_port.send(msg)
            
    def send_stop(self):
        if self.output_port:
            msg = mido.Message('stop')
            self.output_port.send(msg)
