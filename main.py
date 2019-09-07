import mido
import serial
from serial.tools.list_ports import comports

from controller import FDDOrgan
from moppy.bridge import MoppySerialBridge

if __name__ == "__main__":
    keyboard = mido.get_input_names()[0]
    port = comports()[0].device
    ser = serial.Serial(port, 57600)
    bridge = MoppySerialBridge(ser)

    with FDDOrgan(bridge, keyboard) as organ:
        organ.run()
