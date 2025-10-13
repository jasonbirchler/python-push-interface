# Overview

The goal of this project is to create a multitrack, multitimbral MIDI sequencer that is controlled by the Ableton Push 2 and runs on a Raspberry Pi 4 or 5. Requirements follow.

## Requirements

### Architecture

1. The Push communicates with the Pi via USB. Both MIDI and display data will be transferred via this single USB connection
2. The MIDI out from the Push will be used to control the MIDI sequencer running on the Pi
3. The MIDI Sequencer running on the Pi will translate the control data from the Push into MIDI notes, CCs, clock, etc. and send out on the appropriate MIDI channel(s)
4. The user should be able to save patterns and songs to disk on the Pi for later recall.
5. All code will be written in Python for consistency and because [Push2 Python](git+https://github.com/ffont/push2-python.git) is the best library I have found for abstracting the entire UI of the Push (i.e. knobs, buttons, pads, touchstrip, and screen)

### UI

1. User can select a device as a destination for MIDI notes. destinations have the following properties
    
    a. Device name - this is just a friendly name to identify the device
    b. Channel - MIDI channel that the device is set to recieve on
    c. Port - physical MIDI port the device is connected to. For example, USB or 5-pin MIDI out
    d. Mapping - a list of any MIDI CCs that the device receives and a freindly name. For example, [FilterCutoff: 12, FilterResonance: 13]. These are arbitray and specific to the device, but the user will likely need to provide these mappings manually (perhaps via a JSON file, or similar text-based file)
1. The display should show all available devices based on the ones defined in 1d.
1. The user should be able to select a device using navigation buttons on the Push in order to program a pattern of notes or CCs to send to the device
1. The user should be able to use the pads on the Push to input notes in a pattern in either real time while the pattern is playing, or in step sequencer style.
1. The user should be able to select a musical key for the song (e.g. A, B, D#, etc.), and a scale from a list of predefined musical scales
1. The user should be able to connect patterns to create a track - a track is all of the patterns for one device
1. A song should consist of all the tracks the user has created.
1. The user should be able to determine the tempo of the song such that the MIDI clock signal sent to all devices is consistent. The user should also be able to use an incoming MIDI clock signal and forward that clock to all devices.

## Milestones

1. User can select a MIDI channel, and enter notes into a pattern using the knobs, buttons and pads on the Push. The user should receive visual feedback on the Push display. The user should be able to push the play button on the Push and the MIDI notes in the pattern will be output on the correct channel.
1. User can provide device definitions in the form of a JSON file (or similar) such that those devices can be selected and assigned to patterns from the controls of the Push
1. User can create a track by selecting a device and sequencing multiple patterns
1. User can create a song by sequencing multiple tracks
