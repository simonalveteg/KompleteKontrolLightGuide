# The MIT License
# 
# Copyright (c) 2018 Olivier Jacques
# 
# Synthesia Kontrol: an app to light the keys of Native Instruments
#                    Komplete Kontrol MK2 keyboard, driven by Synthesia


# Modified to work with MK1 keyboards

import hid
import mido
from msvcrt import getch


numkeys = 88 #change this to the number of keys on your keyboard
offset = -(108-numkeys+1)
pid = 0x1410 #change this to the product id of your keyboard

def init():
    """Connect to the keyboard, switch all lights off"""
    global bufferC  # Buffer with the full key/lights mapping
    global device

    device=hid.device()
    # 0x17cc: Native Instruments. 0x1410: KK S88 MK1
    device.open(0x17cc, pid)
    device.write([0xa0])
    
    bufferC = [0x00] * numkeys
    notes_off()

    return True

def notes_off():
    """Turn off lights for all notes"""
    bufferC = [0x00] * numkeys
    device.write([0x82] + bufferC)

def accept_notes(port):
    """Only let note_on and note_off messages through."""
    for message in port:
        if message.type in ('note_on', 'note_off'):
            yield message
        if message.type == 'control_change' and message.channel == 0 and message.control == 16:
            if (message.value & 4):
                print ("User is playing")
            if (message.value & 1):
                print ("Playing Right Hand")
            if (message.value & 2):
                print ("Playing Left Hand")
            notes_off()

def LightNote(note, status, channel, velocity):
    """Light a note ON or OFF"""
    key = (note + offset)

    if key < 0 or key >= numkeys:
        return  

    # Determine color
    left        = [0x00] + [0x00] + [0xFF]   # Blue
    left_thumb  = [0x00] + [0x00] + [0x80]   # Lighter Blue
    right       = [0x00] + [0xFF] + [0x00]   # Green
    right_thumb = [0x00] + [0x80] + [0x00]   # Lighter Green
    default = right
    color = default

    # Finger based channel protocol from Synthesia
    # Reference: https://www.synthesiagame.com/forum/viewtopic.php?p=43585#p43585
    if channel == 0:
        # we don't know who or what this note belongs to, but light something up anyway
        color = default
    if channel >= 1 and channel <= 5:
        # left hand fingers, thumb through pinky
        if channel == 1:
            color = left_thumb
        else:
            color = left
    if channel >= 6 and channel <= 10:
        # right hand fingers, thumb through pinky
        if channel == 6:
            color = right_thumb
        else:
            color = right
    if channel == 11:
        # left hand, unknown finger
        color = left
    if channel == 12:
        # right hand, unknown finger
        color = right

    black = [0x00] * 3 
    if status == 'note_on' :
        colors[3*key:3*key+3]=color #set the three colorvalues of the key to desired color
    if status == 'note_off' :
        colors[3*key:3*key+3]=black #set the key back to black
    device.write([0x82] + colors) #changes the color of pressed key

if __name__ == '__main__':
    """Main: connect to keyboard, open midi input port, listen to midi"""
    print ("Connecting to Komplete Kontrol Keyboard")
    connected = init()
    if connected:
        print ("Opening LoopBe input port")
        ports = mido.get_input_names()
        for port in ports:
            if "LoopBe" in port:
                portName = port
        print ("Listening to Midi")
        with mido.open_input(portName) as midiPort:
            black = [0x00] * 3 #color, R + G + B (in this case black)
            colors = black * numkeys #sets the color to all 88 keys (when it gets written to kontrol)       
            for message in accept_notes(midiPort):
                print('Received {}'.format(message))
                LightNote(message.note, message.type, message.channel, message.velocity)
