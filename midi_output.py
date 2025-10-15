import mido
from typing import Optional

class MidiOutput:
    def __init__(self):
        self.output_ports = {}  # Dictionary of port_name -> mido output port
        self.available_ports = []
        self.input_ports = {}
        self.sequencer = None  # Will be set by sequencer
        self._scan_ports()
        self._setup_midi_input()
        
    def _scan_ports(self):
        self.available_ports = mido.get_output_names()
        
    def _setup_midi_input(self):
        """Setup MIDI input for clock sync"""
        try:
            import threading
            input_names = mido.get_input_names()
            for name in input_names:
                if 'Push' not in name and 'Midronome' in name:  # Only listen to Midronome for now
                    try:
                        port = mido.open_input(name)
                        self.input_ports[name] = port
                        self._monitor_input(name, port)
                        print(f"Listening for MIDI clock on: {name}")
                        break  # Only connect to first Midronome port
                    except Exception as e:
                        print(f"Failed to open input {name}: {e}")
        except Exception as e:
            print(f"MIDI input setup failed: {e}")
            
    def _monitor_input(self, port_name, port):
        """Monitor MIDI input for clock messages"""
        print(f"Starting MIDI monitor thread for {port_name}")
        try:
            port.callback = self._handle_midi_message
        except Exception as e:
            print(f"MIDI input monitor error on {port_name}: {e}")
            
    def _handle_midi_message(self, msg):
        """Handle incoming MIDI message"""
        if self.sequencer:
            if msg.type == 'clock':
                self.sequencer.handle_midi_clock()
            elif msg.type == 'start':
                print(f"MIDI Start received")
                self.sequencer.handle_midi_start()
            elif msg.type == 'stop':
                print(f"MIDI Stop received")
                self.sequencer.handle_midi_stop()
            
    def set_sequencer(self, sequencer):
        """Set sequencer reference for clock handling"""
        self.sequencer = sequencer
        
    def connect(self, port_name: Optional[str] = None):
        if port_name is None and self.available_ports:
            port_name = self.available_ports[0]
            
        if port_name and port_name not in self.output_ports:
            # Try exact match first
            actual_port = port_name
            if port_name not in self.available_ports:
                # Try fuzzy matching - find port containing the search term
                matches = [p for p in self.available_ports if port_name.lower() in p.lower()]
                if matches:
                    actual_port = matches[0]
                    print(f"Fuzzy matched '{port_name}' to '{actual_port}'")
                else:
                    print(f"No port found matching '{port_name}'")
                    return False
            
            try:
                self.output_ports[port_name] = mido.open_output(actual_port)  # Use original name as key
                print(f"Connected to MIDI port: {actual_port}")
                return True
            except Exception as e:
                print(f"Failed to connect to MIDI port {actual_port}: {e}")
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
