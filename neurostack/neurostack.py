from devices.muse import Muse
from socketIO_client import SocketIO
from utils import generate_uuid
from sanic import Sanic

import argparse
import json
import socketio
import time


class Neurostack:

    def __init__(self, devices=None):
        """
        Initialize a connection with an EEG device, and sets up an
        asynchronous connection with subscribers passed in.

        :param device: [Devices]
        """
        self.devices = devices

        # sanic server connects to app
        self.sio_app = socketio.AsyncServer(async_mode='sanic')
        self.sio_app_server = Sanic()
        self.sio_app.attach(self.sio_app_server)

        # socketIO client connects to neurostack server
        self.sio_neurostack = None

    #
    # Methods for handling devices
    #

    def start(self, list_of_devices=None):
        """
        Start streaming EEG from device, and publish data to subscribers.

        :param list_of_devices: [Device] List of devices to start streaming. If none, all devices will start streaming.

        :return: None
        """
        if list_of_devices is None:
            devices_to_start = self.devices
        else:
            devices_to_start = list_of_devices

        for device in devices_to_start:
            device.start()

    def stop(self, list_of_devices=None):
        """
        Stop streaming EEG data from device, and stop publishing data to
        subscribers. Connection to device remains intact, and device is not
        turned off.

        :param list_of_devices: [Device] List of devices to stop streaming. If none, all devices will stop streaming.

        :return: None
        """
        if list_of_devices is None:
            devices_to_start = self.devices
        else:
            devices_to_start = list_of_devices

        for device in devices_to_start:
            device.stop()

    def shutdown(self,
                 list_of_devices=None,
                 list_of_subscribers=None,
                 list_of_tags=None):
        """
        Close connection to device, WebSocket connections to publishers, and tag sources.

        :return: None
        """
        pass

    #
    # Methods for handling server-side communication
    #

    def neurostack_connect(self, ip='35.222.93.233', port=8001):
        """
        Connects to neurostack server at ip:port. If no arguments for ip and
        port are given, then connects to the default hardcoded address for a
        server on the cloud.
        """
        self.sio_neurostack = SocketIO(ip, port)
        self.sio_neurostack.connect()

    def neurostack_disconnect(self):
        """Disconnects from neurostack server"""
        self.sio_neurostack.disconnect()

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
        self.sio_neurostack.emit("train_classifier", args, self.on_train_results)
        self.sio_neurostack.wait_for_callbacks(seconds=1)

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
        self.sio_neurostack.emit("retrieve_prediction_results", args, self.on_retrieve_prediction_results)
        self.sio_neurostack.wait_for_callbacks(seconds=1)

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
        self.sio_neurostack.emit("retrieve_prediction_results_test", args, self.print_results)
        self.sio_neurostack.wait_for_callbacks(seconds=1)

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
        self.sio_neurostack.emit("train_classifier_test", args, self.print_results)
        self.sio_neurostack.wait_for_callbacks(seconds=1)

    #
    # Methods for handling client-side communication
    #

    def initialize_handlers(self):
        """Initialize handlers for client-side communication"""
        self.sio_app.on("train", self.train_handler)
        self.sio_app.on("predict", self.predict_handler)
        self.sio_app.on("generate_uuid", self.generate_uuid_handler)

    def run(self, host='localhost', port=8002):
        """
        Runs Neurostack on host:port. This is used as an endpoint for
        client-side communication.

        :param host: local address to Neurostack on
        :param port: port to run Neurostack on
        :return: None
        """
        self.sio_app_server.run(host=host, port=port)

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
    # Other methods
    #

    def get_info(self, list_of_devices=None) -> []:
        """
        Return list of string representations of device info for specified devices (by calling get_info of each device).
        By default lists info of all devices under Neurostack.

        :return:
        """
        if list_of_devices is None:
            devices_to_start = self.devices
        else:
            devices_to_start = list_of_devices

        info = [device.get_info() for device in devices_to_start]
        return info


if __name__ == '__main__':

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Run Neurostack')

    parser.add_argument('--address', type=str, default='localhost:8002',
                        help='ip:port to run Neurostack client on')
    parser.add_argument('--server_address', type=str,
                        help='ip:port of Neurostack server to connect to')

    args = parser.parse_args()

    # TODO: add something to specify which devices get passed in
    muse = Muse()
    muse.connect(fake_data=True)
    muse.start()

    # create and run neurostack!
    devices = [muse]
    neurostack = Neurostack(devices=devices)

    # connect to neurostack server
    if args.server_address is not None:
        ip, port = args.server_address.split(':')
        neurostack.neurostack_connect(ip=ip, port=port)

    # run neurostack client
    neurostack.initialize_handlers()
    host, port = args.address.split(':')
    neurostack.run(host=host, port=port)
