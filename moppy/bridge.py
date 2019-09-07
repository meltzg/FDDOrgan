from time import sleep

from serial import Serial

import moppy.protocol as p


class MoppySerialBridge(object):
    def __init__(self, ser: Serial) -> None:
        self.ser = ser
        self.wait_for_startup()

    def wait_for_startup(self, timeout: int = 10) -> None:
        for i in range(timeout):
            print("attempting to connect to moppy: {}".format(i))
            try:
                self.ping()
                return
            except ValueError:
                sleep(1)

    def ping(self) -> p.SystemPongCommand:
        ping = p.SystemPingCommand()
        self._send_command(ping, 0, 0)
        if not self.ser.in_waiting:
            raise ValueError("No response from serial port")
        preamble = self.ser.read(p.PREAMBLE_LENGTH)
        assert preamble[0] == p.MESSAGE_START

        payload_length = preamble[3]
        payload = self.ser.read(payload_length)
        assert payload[0] == p.SystemPongCommand.command

        return p.SystemPongCommand(*payload[1:])

    def start_sequence(self) -> None:
        self._send_command(p.SystemSequenceStartCommand(), 0, 0)

    def stop_sequence(self) -> None:
        self._send_command(p.SystemSequenceStopCommand(), 0, 0)

    def play_note(
            self, note: int, velocity: int, device_address: int, sub_address: int
    ) -> None:
        command = p.DevicePlayNoteCommand(note_number=note, velocity=velocity)
        self._send_command(command, device_address, sub_address)

    def stop_note(self, note: int, device_address: int, sub_address: int) -> None:
        command = p.DeviceStopNoteCommand(note_number=note)
        self._send_command(command, device_address, sub_address)

    def _send_command(
            self, command: p.BaseMoppyCommand, device_address: int, sub_address: int
    ) -> None:
        message = p.MoppyMessage(
            device_address=device_address, sub_address=sub_address, command=command
        )
        self._send_message(message)

    def _send_message(self, message: p.MoppyMessage) -> None:
        print("sending message {}".format(message.render()))
        self.ser.write(message.render())
