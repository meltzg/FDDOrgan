import typing as t

MESSAGE_START = 0x4D
PREAMBLE_LENGTH = 4


class BaseMoppyCommand(object):
    command = -1

    def __repr__(self) -> str:
        payload_repr = ", ".join(
            "{}={}".format(slot, getattr(self, slot))
            for slot in getattr(self, "__slots__", [])
        )
        return "[command={}, length={}, payload=[{}]".format(
            self.command, self.length, payload_repr
        )

    @property
    def length(self) -> int:
        return len(getattr(self, "__slots__", [])) + 1

    def to_list(self) -> t.List[int]:
        payload = getattr(self, "__slots__", [])
        payload = [getattr(self, slot) for slot in payload]
        return [self.length, self.command] + payload


class SystemPingCommand(BaseMoppyCommand):
    command = 0x80


class SystemPongCommand(BaseMoppyCommand):
    command = 0x81

    __slots__ = ["device_address", "min_sub_address", "max_sub_address"]

    def __init__(
            self, device_address: int, min_sub_address: int, max_sub_address: int
    ) -> None:
        self.device_address = device_address
        self.min_sub_address = min_sub_address
        self.max_sub_address = max_sub_address


class SystemResetCommand(BaseMoppyCommand):
    command = 0xFF


class SystemSequenceStartCommand(BaseMoppyCommand):
    command = 0xFA


class SystemSequenceStopCommand(BaseMoppyCommand):
    command = 0xFC


class DeviceResetCommand(BaseMoppyCommand):
    command = 0x00


class DeviceStopNoteCommand(BaseMoppyCommand):
    command = 0x08

    __slots__ = ["note_number"]

    def __init__(self, note_number: int) -> None:
        self.note_number = note_number


class DevicePlayNoteCommand(BaseMoppyCommand):
    command = 0x09

    __slots__ = ["note_number", "velocity"]

    def __init__(self, note_number: int, velocity: int = 0) -> None:
        self.note_number = note_number
        self.velocity = velocity


class DeviceBendPitch(BaseMoppyCommand):
    command = 0x0E

    __slots__ = ["msb", "lsb"]

    def __init__(self, msb: int, lsb: int) -> None:
        self.msb = msb
        self.lsb = lsb


class MoppyMessage(t.NamedTuple):
    device_address: int
    sub_address: int
    command: BaseMoppyCommand

    def render(self) -> bytes:
        full_message = [
                           MESSAGE_START,
                           self.device_address,
                           self.sub_address,
                       ] + self.command.to_list()
        byte_message = [val.to_bytes(1, byteorder="little") for val in full_message]
        return b"".join(byte_message)
