import typing as t

import mido

from moppy.bridge import MoppySerialBridge


class FDDOrgan(object):
    def __init__(self, bridge: MoppySerialBridge, midi_inport_name: str) -> None:
        self.bridge = bridge
        self.midi_inport_name = midi_inport_name
        self.midi_inport = None

        self.bridge.wait_for_startup()
        self.configuration = self.bridge.ping()

        self.available_sub_addresses = set(
            range(
                self.configuration.min_sub_address,
                self.configuration.max_sub_address + 1,
            )
        )
        self.note_locations: t.Dict[int, int] = {}

    def __enter__(self):
        self.midi_inport = mido.open_input(self.midi_inport_name)
        self.bridge.start_sequence()
        print("organ config: {}".format(self.configuration))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.midi_inport.close()
        self.bridge.stop_sequence()

    def run(self) -> None:
        if not self.configuration or not self.midi_inport:
            raise ValueError("Midi port has not been opened")

        try:
            for message in self.midi_inport:
                if message.type == "note_on":
                    sub_address = self._claim_available_sub_address(message.note)
                    if not sub_address:
                        print("no available sub addresses")
                        continue
                    self.bridge.play_note(
                        message.note,
                        message.velocity,
                        self.configuration.device_address,
                        sub_address,
                    )
                elif message.type == "note_off":
                    sub_address = self._free_note(message.note)
                    if sub_address > 0:
                        self.bridge.stop_note(
                            message.note, self.configuration.device_address, sub_address
                        )
                else:
                    continue
        except Exception as e:
            print(e)

    def _claim_available_sub_address(self, note_number: int) -> t.Union[int, None]:
        if not self.available_sub_addresses:
            return None
        sub_address = self.available_sub_addresses.pop()
        self.note_locations[note_number] = sub_address
        return sub_address

    def _free_note(self, note_number: int) -> int:
        if note_number in self.note_locations:
            sub_address = self.note_locations.pop(note_number)
            self.available_sub_addresses.add(sub_address)
            return sub_address
        return -1
