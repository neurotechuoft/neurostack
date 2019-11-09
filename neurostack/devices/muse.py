from data_streams.eeg_stream import EEGStream
from data_streams.marker_stream import MarkerStream
from data_streams.ml_stream import MLStream
from devices import Device
from sanic import Sanic
from socketIO_client import SocketIO
from utils import generate_uuid

import json
import pylsl
import random
import socketio
import threading
import time
import warnings


class Muse(Device):

    def __init__(self, device_id=None):
        super().__init__(device_id)
        self.streams = {}
        self.pred_results = []
        self.train_results = []
        self.time_diff = 0      # difference between unix and muse time
        self.train_mode = True  # True for training, False for prediction

        # socket for communicating with whatever wants to pull prediction
        # results from Muse
        self.sio = socketio.AsyncServer(async_mode='sanic')
        self.app = Sanic()
        self.sio.attach(self.app)

        # for generating fake data
        self._fake_muse = None
        self._fake_muse_active = False

    @staticmethod
    def available_devices():
        pass

    #
    # Callback functions
    #

    def on_retrieve_prediction_results(self, *args):
        """Callback function for saving prediction results"""
        results = args[0]
        self.pred_results.append(results)

    def on_train_results(self, *args):
        """Callback function for saving training results"""
        results = args[0]
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

    def _create_fake_eeg_stream(self):
        """
        Method for generating dummy EEG data for the muse. Sends randomly-
        generated data through an LSL outlet.

        :return: None
        """
        def generate_muse_data():
            """Generate 4 random floats, representing channels AF7, AF8, TP9,
            and TP10 on the muse headset"""
            return [random.random() for _ in range(4)]

        # create fake muse
        info = pylsl.StreamInfo(name='Muse', type='EEG', channel_count=4,
                                nominal_srate=256, channel_format='float32', source_id='fake muse')
        info.desc().append_child_value('manufacturer', 'Muse')
        channels = info.desc().append_child('channels')

        # set channel names and units
        for c in ['TP9-l_ear', 'FP1-l_forehead', 'FP2-r_forehead',
                  'TP10-r_ear']:
            channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "EEG")

        outlet = pylsl.StreamOutlet(info)

        # continuously push data to outlet when active
        while self._fake_muse_active:
            outlet.push_sample(generate_muse_data())
            time.sleep(0.00390625)  # 256Hz

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
        self.socket_client.emit("train_classifier", args, self.on_train_results)
        self.socket_client.wait_for_callbacks(seconds=1)

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
        self.socket_client.emit("retrieve_prediction_results", args, self.on_retrieve_prediction_results)
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

    def send_predict_data_test(self, uuid, eeg_data):
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

    def send_train_data_test(self, uuid, eeg_data, p300):
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

    #
    # Methods for handling client-side communication
    #

    def initialize_handlers(self):
        """Initialize handlers for client-side communication"""
        self.sio.on("train", self.train_handler)
        self.sio.on("predict", self.predict_handler)

        self.sio.on("generate_uuid", self.generate_uuid_handler)

    async def train_handler(self, sid, args):
        """Handler for passing training data to Neurostack"""
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
            str(uuid)       # epoch ID
        ]
        self.marker_outlet.push_sample(package)
        await self.start_event_loop()

        while len(self.train_results) == 0:
            time.sleep(.1)
        return self.train_results.pop(0)

    async def predict_handler(self, sid, args):
        """Handler for passing prediction data to Neurostack"""
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
            str(uuid)       # epoch ID
        ]
        self.marker_outlet.push_sample(package)
        await self.start_event_loop()

        while len(self.pred_results) == 0:
            time.sleep(.1)
        return self.pred_results.pop(0)

    async def generate_uuid_handler(self, sid, args):
        """Handler for sending a request to the server to generate a UUID"""
        return generate_uuid()

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
                    self.send_train_data(uuid, train_data, train_targets)
                    return

            # send prediction jobs to server
            else:
                data = self.streams['ml'].get_prediction_data()
                if data is not None:
                    uuid = data['uuid']
                    eeg_data = data['eeg_data']
                    self.send_predict_data(uuid, eeg_data)
                    return

            time.sleep(0.1)

    #
    # Public device methods
    #

    def connect(self, device_id=None, fake_data=False):
        """
        Creates data streams if there are none and connects to EEG stream
        (since that is the one that is immediately needed for use). If fake_data
        is True, then start a separate thread that generates fake data instead
        of connecting to a muse.
        """
        if self.streams.get('eeg') is None:
            self.streams['eeg'] = self._create_eeg_stream()

        if self.streams.get('marker') is None:
            self.streams['marker'] = self._create_marker_stream()

        if self.streams.get('ml') is None:
            data = {'event_time': 0.4,
                    'train_epochs': 120}    # 120 for 2 min, 240 for 4 min
            self.streams['ml'] = self._create_ml_stream(data)

        # create thread that runs something which continuously streams data
        if fake_data:
            eeg_data_thread = threading.Thread(target=self._create_fake_eeg_stream,
                                               name='fake muse')
            eeg_data_thread.daemon = True
            eeg_data_thread.start()

            self._fake_muse_active = True
            self._fake_muse = eeg_data_thread

        self.streams['eeg'].lsl_connect()

    def start(self):
        """Start streaming EEG data"""
        self.streams['eeg'].start()

        while len(self.streams['eeg'].data) == 0:
            time.sleep(0.1)

        self.time_diff = time.time() - self.streams['eeg'].data[-1][-1]

    def stop(self):
        """Stop streaming EEG data"""
        self.streams['eeg'].stop()

    def shutdown(self):
        """Disconnect EEG stream (and stop streaming data)"""
        for stream_name in ['eeg', 'marker', 'ml']:
            self.streams[stream_name] = None

    def get_info(self):
        pass
