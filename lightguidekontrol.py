import pywinusb.hid as pyhid
import mido
import time
import hid
#from msvcrt import getch
'''
Based on the work of anykey, jasonbrent and OlvierJ. Feel free to modify in any way.

A small script to have the lights on the keyboard light up only when the corresponding key gets pressed.
Problem right now: only one key can light up at a time :/

Made for Komplete Kontrol S88 MK1
'''


numkeys = 88 #my keyboard has 88 keys
pid = 0x1410 #product ID of your keyboard
offset = 108 - numkeys + 1 #this is based on the fact that my 88 keys has an offset of 21, and Olivier's 61 key has an offset of 48. 20+88=108, 60+48=108.


def init():
    #Connect to keyboard and switch lights off
    global bufferC
    global kontrol
    
    kontrol = hid.device()
    # filter connected HID devices and check if keyboard is connected 
    # 0x17cc: Native Instruments. 0x1410: KK S88 MK1.
    filter = pyhid.HidDeviceFilter(vendor_id = 0x17cc, product_id = pid).get_devices()
    if filter:
        print("Komplete Kontrol Found!")
        kontrol.open(0x17cc, pid)
        kontrol.write([0xa0]) # activates the device
        notes_off()
        print("Lights turned off..")
        midi_connection()
    else:
        print("Could not find keyboard :c")
        
def notes_off():
    #sets keylights to black
    bufferC = [0x00] * 3 * numkeys
    kontrol.write([0x82] + bufferC)
    #code below sets other buttons to a dimmed white, not really neccesary
    '''bufferC = [0x0F] * 24 
    kontrol.write([0x80] + bufferC)'''

       
def accept_notes(port):
    """Only let note_on and note_off messages through."""
    for message in port:
        if message.type in ('note_on', 'note_off'):
            yield message
            
#anykeys demosweep, not necessary but it's nice
def CoolDemoSweep(loopcount):
    speed = 0.01
    for loop in range(0,loopcount):
        for x in range(0, numkeys):
            bufferC = [0x00] * 3 * numkeys
            bufferC[0] = 0x82
            bufferC[x*3-2] = 0xFF
            kontrol.write(bufferC)
            time.sleep(speed)
        for x in range(numkeys, 0,-1):
            bufferC = [0x00] * 3 * numkeys
            bufferC[0] = 0x82
            bufferC[x*3-2] = 0xFF
            kontrol.write(bufferC)
            time.sleep(speed)
    notes_off()
   
def midi_connection():
    ports = mido.get_input_names()
    for port in ports: #cycle through all ports until Komplete Kontrol is found
        CoolDemoSweep(1)  # Sweep 1x Red on the keys for fun
        if "Komplete Kontrol" in port:
            portName = port
        print ("Listening to Midi")
        with mido.open_input(portName) as midiPort:
            black = [0x00] * 3 #color, R + G + B (in this case black)
            colors = black * numkeys #sets the color to all 88 keys (when it gets written to kontrol)
            #the color has to be sent in to the input function for multiple keys to light up at the same time
            for message in accept_notes(midiPort): #detects input on KK
                print('Received {}'.format(message))
                input(message.note, message.type, message.velocity, colors)

def input(note,status,velocity,colors):
    key = note-offset
    black = [0x00] * 3 
    color = [0xFF] + [0x00] + [0x00] #the color to give the pressed key
    #print(colors) #for troubleshooting
    if status == 'note_on' :
        colors[3*key:3*key+3]=color #set the three colorvalues of the key to desired color
    if status == 'note_off' :
        colors[3*key:3*key+3]=black #set the key back to black
    kontrol.write([0x82] + colors) #changes the color of pressed key

init()

