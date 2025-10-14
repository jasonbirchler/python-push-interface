import mido
from typing import Optional

class MidiOutput:
    def __init__(self):
        self.output_ports = {}  # Dictionary of port_name -> mido output port
        self.available_ports = []
        self._scan_ports()
        
    def _scan_ports(self):
        self.available_ports = mido.get_output_names()
        
    def connect(self, port_name: Optional[str] = None):
        if port_name is None and self.available_ports:
            port_name = self.available_ports[0]
            
        if port_name and port_name not in self.output_ports:
            try:
                self.output_ports[port_name] = mido.open_output(port_name)
                print(f"Connected to MIDI port: {port_name}")
                return True
            except Exception as e:
                print(f"Failed to connect to MIDI port {port_name}: {e}")
                return False
        return port_name in self.output_ports
        
    def disconnect(self, port_name: Optional[str] = None):
        if port_name:
            if port_name in self.output_ports:
                self.output_ports[port_name].close()
                del self.output_ports[port_name]
        else:
            # Disconnect all ports
            for port in self.output_ports.values():
                port.close()
            self.output_ports.clear()
            
    def send_note_on(self, channel: int, note: int, velocity: int, port_name: Optional[str] = None):
        target_ports = [self.output_ports[port_name]] if port_name and port_name in self.output_ports else self.output_ports.values()
        msg = mido.Message('note_on', channel=channel-1, note=note, velocity=velocity)
        for port in target_ports:
            port.send(msg)

            
    def send_note_off(self, channel: int, note: int, port_name: Optional[str] = None):
        target_ports = [self.output_ports[port_name]] if port_name and port_name in self.output_ports else self.output_ports.values()
        msg = mido.Message('note_off', channel=channel-1, note=note, velocity=0)
        for port in target_ports:
            port.send(msg)
            
    def send_cc(self, channel: int, cc_number: int, value: int, port_name: Optional[str] = None):
        target_ports = [self.output_ports[port_name]] if port_name and port_name in self.output_ports else self.output_ports.values()
        msg = mido.Message('control_change', channel=channel-1, control=cc_number, value=value)
        for port in target_ports:
            port.send(msg)

    def send_clock(self):
        msg = mido.Message('clock')
        for port in self.output_ports.values():
            port.send(msg)

            
    def send_start(self):
        msg = mido.Message('start')
        for port in self.output_ports.values():
            port.send(msg)
            
    def send_stop(self):
        msg = mido.Message('stop')
        for port in self.output_ports.values():
            port.send(msg)
