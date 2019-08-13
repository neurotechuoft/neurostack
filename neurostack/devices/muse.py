from data_streams import EEGStream
from devices import Device
from socketIO_client import SocketIO

import warnings


class Muse(Device):

    def __init__(self, device_id=None):
        super().__init__(device_id)
        self.streams = {}
        self.pred_results = []
        self.train_results = []
        self.time_diff = 0      # difference between unix and muse time
        self.train_mode = True  # True for training, False for prediction

    @staticmethod
    def available_devices():
        pass

    #
    # Callback functions
    #

    def on_retrieve_prediction_results(self, *args):
        """Callback function for saving prediction results"""
        results=args[1]
        self.pred_results.append(results)

    def on_train_results(self, *args):
        """Callback function for saving training results"""
        results=args[1]
        self.train_results.append(results)

    def print_results(self, *args):
        """Test callback function that simply prints out the results"""
        for arg in args:
            print(arg)

    #
    # Private device methods for handling data streams
    #

    def _create_eeg_stream(self):
        """Creates a stream that streams EEG data"""
        return EEGStream(thread_name='EEG_data', event_channel_name='P300')

    def _create_marker_stream(self):
        """Create a stream that streams marker data"""
        info = pylsl.StreamInfo('Markers', 'Markers', 4, 0, 'string', 'mywid32')
        self.marker_outlet = pylsl.StreamOutlet(info)
        return MarkerStream(thread_name='Marker_stream')

    def _create_ml_stream(self, data):
        """Creates a stream that combines the EEG and marker streams, and
        forms epochs based on timestamp"""
        if self.streams.get('eeg') is None:
            raise Exception(f"EEG stream does not exist")
        if self.streams.get('marker') is None:
            raise Exception(f"Marker stream does not exist")

        return MLStream(m_stream=self.streams['marker'],
                        eeg_stream=self.streams['eeg'],
                        event_time=data['event_time'],
                        train_epochs=data['train_epochs'])

    def _start_stream(self, stream):
        """Starts stream given stream name (one of 'eeg', 'marker', or 'ml')"""
        if self.streams.get(stream) is None:
            raise RuntimeError("Cannot start {0} stream, stream does not exist".format(stream))
        elif stream == 'ml':
            self.streams[stream].start(self.train_mode)
        else:
            self.streams[stream].lsl_connect()

    def _stop_stream(self, stream):
        """Stops stream given stream name (one of 'eeg', 'marker', or 'ml')"""
        if self.streams.get(stream) is None:
            raise RuntimeError("Cannot stop {0} stream, stream does not exist".format(stream))
        else:
            self.streams[stream].stop()

    #
    # Methods for handling server communication
    #

    def neurostack_connect(self, ip='35.222.93.233', port=8001):
        """
        Connects to neurostack server at ip:port and starts marker and ML
        streams. If no arguments for ip and port are given, then connects to
        the default hardcoded address for a server on the cloud.
        """
        self.socket_client = SocketIO(ip, port)
        self.socket_client.connect()

        # assumes EEG stream has already been started
        for stream in ['marker', 'ml']:
            self._start_stream(stream)

        while len(self.streams['eeg'].data) == 0:
            time.sleep(0.1)

        self.time_diff = time.time() - self.streams['eeg'].data[-1][-1]

    def neurostack_disconnect(self):
        """Disconnects from neurostack server and stops marker and ML streams"""
        for stream in ['marker', 'ml']:
            self._stop_stream(stream)

        self.socket_client.disconnect()

    def send_predict_data(self, uuid, eeg_data):
        """
        Sneds prediction data to neurostack server

        :param uuid: client's UUID
        :param eeg_data: one sample of EEG data that we want to predict for
        :returns: None
        """
        args = {
            'uuid': uuid,
            'data': eeg_data
        }
        self.socket_client.emit("retrieve_prediction_results", data, self.on_retrieve_prediction_results)
        self.socket_client.wait_for_callbacks(seconds=1)

    def send_train_data(self, uuid, eeg_data, p300):
        """
        Sends training data to neurostack server

        :param uuid: client's UUID
        :param eeg_data: one sample of EEG data to be used for training
        :param p300: True if this data represents a p300 signal, else False
        :returns: None
        """
        args = {
            'uuid': uuid,
            'data': eeg_data,
            'p300': p300
        }
        self.socket_client.emit("train_classifier", data, self.on_train_results)
        self.socket_client.wait_for_callbacks(seconds=1)

    def change_mode(self, train_mode=False):
        """
        self.train_mode=True for training mode
        self.train_mode=False for prediction mode
        """
        if self.streams['ml'] is None:
            raise Exception(f"ml stream does is not running")

        curr_mode = self.streams['ml'].get_mode()
        if curr_mode is not train_mode:
            self.train_mode = train_mode
            self.streams['ml'].set_mode(train_mode)

    async def train(self, sid, args):
        if not self.train_mode:
            self.change_mode(train_mode=True)
            time.sleep(.2)

        args = json.loads(args)
        uuid = args['uuid']
        timestamp = args['timestamp']
        p300 = args['p300']

        timestamp -= self.time_diff
        package = [
            str(timestamp),
            str(p300),      # target
            str(1),         # 1 event total
            str(uuid)       # take uuid for epoch id
        ]
        self.marker_outlet.push_sample(package)
        await self.start_event_loop()

        while len(self.train_results) == 0:
            time.sleep(.1)
        score = self.train_results.pop(0)
        return sid, score

    async def predict_handler(self, sid, args):
        if self.train_mode:
            self.change_mode(train_mode=False)
            time.sleep(.2)

        args = json.loads(args)
        uuid = args['uuid']
        timestamp = args['timestamp']

        timestamp -= self.time_diff
        package = [
            str(timestamp),
            str(0),         # target
            str(1),         # 1 event total
            str(uuid)       # take uuid for epoch id
        ]
        self.marker_outlet.push_sample(package)
        await self.start_event_loop()

        while len(self.pred_results) == 0:
            time.sleep(.1)
        pred = self.pred_results.pop(0)
        uuid, p300, score = pred
        results = {'uuid': uuid, 'p300': p300, 'score': score}
        return sid, results

    def send_predict_data(self, uuid, eeg_data):
        """
        Tests endpoint for sending prediction data to neurostack server

        :param uuid: client's UUID
        :param eeg_data: one sample of EEG data that we want to predict for
        :returns: None
        """
        args = {
            'uuid': uuid,
            'data': eeg_data
        }
        self.socket_client.emit("retrieve_prediction_results_test", args, self.print_results)
        self.socket_client.wait_for_callbacks(seconds=1)

    def send_train_data(self, uuid, eeg_data, p300):
        """
        Tests endpoint for sending training data to neurostack server

        :param uuid: client's UUID
        :param eeg_data: one sample of EEG data to be used for training
        :param p300: True if this data represents a p300 signal, else False
        :returns: None
        """
        args = {
            'uuid': uuid,
            'data': eeg_data,
            'p300': p300
        }
        self.socket_client.emit("train_classifier_test", args, self.print_results)
        self.socket_client.wait_for_callbacks(seconds=1)

    async def start_event_loop(self):
        """
        Continuously pulls data from ml_stream and sends to server based on
        whether we are training or predicting
        """
        if self.streams.get('ml') is None:
            raise Exception(f"ml stream does not exist")

        data = None
        while data is None:
            # send training jobs to server
            if self.train_mode:
                data = self.streams['ml'].get_training_data()
                if data is not None:
                    uuid = data['uuid']
                    train_data = data['train_data']
                    train_targets = data['train_targets']
                    self.train(uuid, train_data, train_targets)
                    return

            # send prediction jobs to server
            else:
                data = self.streams['ml'].get_prediction_data()
                if data is not None:
                    uuid = data['uuid']
                    eeg_data = data['eeg_data']
                    self.predict(uuid, eeg_data)
                    return

            time.sleep(0.1)

    #
    # Public device metods
    #

    def connect(self, device_id=None):
        """
        Creates data streams if there are none and connects to EEG stream
        (since that is the one that is immediately needed for use)
        """
        if self.streams.get('eeg') is None:
            self.streams['eeg'] = self._create_eeg_stream()

        if self.streams.get('marker') is None:
            self.streams['marker'] = self._create_marker_stream()

        if self.streams.get('ml') is None:
            data = {'event_time': 0.4,
                    'train_epochs': 120}    # 120 for 2 min, 240 for 4 min
            self.streams['ml'] = self._create_ml_stream(data)

        self.streams['eeg'].lsl_connect()

    def start(self):
        """Start streaming EEG data"""
        self.streams['eeg'].start()

    def stop(self):
        """Stop streaming EEG data"""
        self.streams['eeg'].stop()

    def shutdown(self):
        """Disconnect EEG stream (and stop streaming data)"""
        self.streams['eeg'] = None

    def get_info(self):
        pass
