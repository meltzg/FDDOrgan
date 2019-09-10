import logging
import typing as t

import mido

from moppy.bridge import MoppySerialBridge

logger = logging.getLogger(__name__)


class FDDOrgan(object):
    def __init__(self, bridge: MoppySerialBridge, midi_inport_name: str) -> None:
        self.bridge = bridge
        self.midi_inport_name = midi_inport_name
        self.midi_inport = None

        self.bridge.wait_for_startup()
        self.configuration = self.bridge.ping()

        self.available_sub_addresses = sorted(
            range(
                self.configuration.min_sub_address,
                self.configuration.max_sub_address + 1,
            )
        )
        self.note_locations: t.Dict[int, int] = {}

    def __enter__(self):
        self.midi_inport = mido.open_input(self.midi_inport_name)
        self.bridge.start_sequence()
        logger.info("organ config: %s", self.configuration)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.midi_inport.close()
        self.bridge.stop_sequence()

    def run(self) -> None:
        consecutive_unknown = 0
        if not self.configuration or not self.midi_inport:
            raise ValueError("Midi port has not been opened")

        try:
            for message in self.midi_inport:
                unknown = False
                if message.type == "note_on":
                    sub_address = self._claim_available_sub_address(message.note)
                    if not sub_address:
                        logger.debug("no available sub addresses")
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
                elif message.type == "pitchwheel":
                    self.bridge.bend_pitch(message.pitch, self.configuration)
                else:
                    unknown = True
                    logger.debug('unknown command %s', message)

                if not unknown:
                    consecutive_unknown = 0
                else:
                    consecutive_unknown += 1
                if consecutive_unknown > 3:
                    consecutive_unknown = 0
                    self.bridge.reset()
        except KeyboardInterrupt as e:
            pass

    def _claim_available_sub_address(self, note_number: int) -> t.Union[int, None]:
        if not self.available_sub_addresses:
            return None
        sub_address = self.available_sub_addresses[0]
        self.available_sub_addresses = self.available_sub_addresses[1:]
        self.note_locations[note_number] = sub_address
        return sub_address

    def _free_note(self, note_number: int) -> int:
        if note_number in self.note_locations:
            sub_address = self.note_locations.pop(note_number)
            i = 0
            for i in range(len(self.available_sub_addresses)):
                if self.available_sub_addresses[i] > sub_address:
                    break
            self.available_sub_addresses.insert(i, sub_address)
            return sub_address
        return -1
