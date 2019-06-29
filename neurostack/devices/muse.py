from data_streams import EEG_stream
from devices import Device

import warnings


class Muse(Device):

    def __init__(self, device_id=None):
        super().__init__(device_id=device_id)
        self.streams = {}

    #
    # Private device methods for handling data streams and server connections
    #

    def _create_eeg_stream():
        return EEGStream(thread_name='EEG_data', event_channel_name='P300')

    #
    # Public device metods
    #

    def connect(self, device_id=None):
        """ Creates an EEG stream if there are none and connects to it. """
        if self.streams.get('eeg') is None:
            self.streams['eeg'] = self._create_eeg_stream()

        self.streams['eeg'].lsl_connect()

    def start(self):
        """ Start streaming EEG data """
        self.streams['eeg'].start()

    def stop(self):
        """ Stop streaming EEG data """
        self.streams['eeg'].stop()

    def shutdown(self):
        """ Disconnect EEG stream (and stop streaming data) """
        self.streams['eeg'] = None

    def get_info(self):
        pass
