import mido
import serial
from serial.tools.list_ports import comports

from moppy.protocol import (
    SystemSequenceStartCommand,
    SystemSequenceStopCommand,
    DevicePlayNoteCommand,
    DeviceStopNote,
    MoppyMessage,
)

if __name__ == '__main__':
    keyboard = mido.get_input_names()[0]
    port = comports()[0].device
    ser = serial.Serial(port, 57600)

    sequence_start = MoppyMessage(
        device_address=0,
        sub_address=0,
        command=SystemSequenceStartCommand()
    )
    sequence_stop = MoppyMessage(
        device_address=0,
        sub_address=0,
        command=SystemSequenceStopCommand()
    )

    ser.write(sequence_start.render())
    with mido.open_input(keyboard) as inport:
        for message in inport:
            if message.type == 'note_on':
                command = DevicePlayNoteCommand(
                    note_number=message.note,
                    velocity=10
                )
            elif message.type == 'note_off':
                command = DeviceStopNote(
                    note_number=message.note,
                )
            else:
                continue
            message = MoppyMessage(
                device_address=1,
                sub_address=1,
                command=command,
            )
            ser.write(message.render())
    ser.write(sequence_stop.render())
