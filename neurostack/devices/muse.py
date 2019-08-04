from data_streams import EEGStream
from devices import Device

import warnings


class Muse(Device):

    def __init__(self, device_id=None):
        super().__init__(device_id)
        self.streams = {}
        self.pred_results = []
        self.train_results = []

    @staticmethod
    def available_devices():
        pass

    #
    # Callback functions
    #

    def on_retrieve_prediction_results(self, *args):
        results=args[1]
        self.pred_results.append(results)

    def on_train_results(self, *args):
        results=args[1]
        self.train_results.append(results)

    #
    # Private device methods for handling data streams
    #

    def _create_eeg_stream(self):
        """ Creates a stream that streams EEG data """
        return EEGStream(thread_name='EEG_data', event_channel_name='P300')

    def _create_marker_stream(self):
        """ Create a stream that streams marker data """
        info = pylsl.StreamInfo('Markers', 'Markers', 4, 0, 'string', 'mywid32')
        self.marker_outlet = pylsl.StreamOutlet(info)
        return MarkerStream(thread_name='Marker_stream')

    def _create_ml_stream(self, data):
        """ Creates a stream that combines the EEG and marker streams, and
        forms epochs based on timestamp """
        if self.streams.get('eeg') is None:
            raise Exception(f"EEG stream does not exist")
        if self.streams.get('marker') is None:
            raise Exception(f"Marker stream does not exist")

        return MLStream(m_stream=self.streams['marker'],
                        eeg_stream=self.streams['eeg'],
                        event_time=data['event_time'],
                        train_epochs=data['train_epochs'])

    def _start_stream(self, stream):
        if self.streams.get(stream) is None:
            raise RuntimeError("Cannot start {0} stream, stream does not exist".format(stream))
        elif stream == 'ml':
            self.streams[stream].start(self.train_mode)
        else:
            self.streams[stream].lsl_connect()

    #
    # Methods for handling server communication
    #

    def predict(self, uuid, eeg_data):
        data = (uuid, eeg_data)
        self.socket_client.emit("retrieve_prediction_results", data, self.on_retrieve_prediction_results)
        self.socket_client.wait_for_callbacks(seconds=1)

    def train(self, uuid, eeg_data, p300):
        data = (uuid, eeg_data, p300)
        self.socket_client.emit("train_classifier", data, self.on_train_results)
        self.socket_client.wait_for_callbacks(seconds=1)

    #
    # Public device metods
    #

    def connect(self, device_id=None):
        """ Creates data streams if there are none and connects to them """
        if self.streams.get('eeg') is None:
            self.streams['eeg'] = self._create_eeg_stream()

        if self.streams.get('marker') is None:
            self.streams['marker'] = self._create_marker_stream()

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
