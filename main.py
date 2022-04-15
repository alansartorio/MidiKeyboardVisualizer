#!/usr/bin/env python3

import jack
import struct
from window import Window

client = jack.Client("MIDI-Viewer")
port = client.midi_inports.register("input")
window = Window()

NOTEON = 0x9
NOTEOFF = 0x8

def onKeyPressed(pitch):
    window.keyPressed(pitch)
def onKeyReleased(pitch):
    window.keyReleased(pitch)

@client.set_process_callback
def process(frames):
    for offset, data in port.incoming_midi_events():
        if len(data) == 3:
            status, pitch, vel = struct.unpack('3B', data)
            if status >> 4 in (NOTEON, NOTEOFF):
                down = status >> 4 == NOTEON
                if down:
                    onKeyPressed(pitch)
                else:
                    onKeyReleased(pitch)
with client:
    #client.connect('a2j:ProdipeMIDIlilo [24] (capture): ProdipeMIDIlilo MIDI 1', port)
    window.run()
