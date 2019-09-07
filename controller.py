import mido

from moppy.bridge import MoppySerialBridge


class FDDOrgan(object):
    def __init__(self, bridge: MoppySerialBridge, midi_inport_name: str) -> None:
        self.bridge = bridge
        self.midi_inport_name = midi_inport_name
        self.midi_inport = None
        self.configuration = None

    def __enter__(self):
        self.midi_inport = mido.open_input(self.midi_inport_name)
        self.bridge.wait_for_startup()
        self.bridge.start_sequence()
        self.configuration = self.bridge.ping()
        print('organ config: {}'.format(self.configuration))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.midi_inport.close()
        self.bridge.stop_sequence()

    def run(self) -> None:
        if not self.configuration or not self.midi_inport:
            raise ValueError('Midi port has not been opened')

        try:
            for message in self.midi_inport:
                if message.type == 'note_on':
                    self.bridge.play_note(message.note, message.velocity, self.configuration.device_address, 1)
                elif message.type == 'note_off':
                    self.bridge.stop_note(message.note, self.configuration.device_address, 1)
                else:
                    continue
        except Exception as e:
            print(e)
