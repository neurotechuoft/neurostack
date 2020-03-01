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
        self.sio_app = socketio.AsyncServer(async_mode='sanic', cors_allowed_origins='*')
        self.sio_app_server = Sanic()
        self.sio_app.attach(self.sio_app_server)

        # socketIO client connects to neurostack server
        self.sio_neurostack = None

        self.train_results = {}
        self.predict_results = {}

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

    def shutdown(self, list_of_devices=None):
        """
        Close connection to device, WebSocket connections to publishers, and tag sources.

        :return: None
        """
        pass

    #
    # Methods for handling server-side communication
    #

    def neurostack_connect(self, ip='neurostack.neurotechuoft.com', port=8001):
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
        self.sio_neurostack.emit("retrieve_prediction_results", args, self.on_predict_results)
        self.sio_neurostack.wait_for_callbacks(seconds=1)

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
        args = json.loads(args)
        uuid = args['uuid']
        timestamp = args['timestamp']
        p300 = args['p300']
        # TODO: check type of p300 (I believe it has to be 0 or 1?)

        # create list for uuid if not done already
        self.train_results[uuid] = self.train_results.get(uuid, [])

        # TODO: change API to specify device
        device = self.devices[0]

        # Wait until the device has enough data (ie. the time slice is complete)
        # then take 100ms - 750ms window for training
        while time.time() < timestamp + 0.75:
            time.sleep(.01)

        timestamp -= self.devices[0].get_time_diff()
        data_dict = device.data_stream.get_eeg_data(start_time=timestamp + .1,
                                                    num_samples=128)
        data = list(data_dict.values())

        self.send_train_data(uuid, data, p300)

        # wait for results
        while len(self.train_results[uuid]) == 0:
            time.sleep(.01)
        result = self.train_results[uuid].pop(0)
        await self.sio_app.emit("train", result)

    async def predict_handler(self, sid, args):
        """Handler for passing prediction data to Neurostack"""
        args = json.loads(args)
        uuid = args['uuid']
        timestamp = args['timestamp']

        # create list for uuid if not done already
        self.predict_results[uuid] = self.predict_results.get(uuid, [])

        # TODO: change API to specify device
        device = self.devices[0]

        # Wait until the device has enough data (ie. the time slice is complete)
        # then take 100ms - 750ms window for training. The window should
        # contain 0.65s * 256Hz = 166 samples.
        while time.time() < timestamp + 0.75:
            time.sleep(.01)

        timestamp -= self.devices[0].get_time_diff()
        data_dict = device.data_stream.get_eeg_data(start_time=timestamp + .1,
                                                    num_samples=128)
        data = list(data_dict.values())

        self.send_predict_data(uuid, data)

        # wait for results
        while len(self.predict_results[uuid]) == 0:
            time.sleep(.01)
        result =  self.predict_results[uuid].pop(0)
        await self.sio_app.emit("predict", result)

    async def generate_uuid_handler(self, sid, args):
        """Handler for sending a request to the server to generate a UUID"""
        uuid = generate_uuid()
        await self.sio_app.emit('generate_uuid', uuid)

    #
    # Callback functions
    #

    def on_train_results(self, *args):
        """Callback function for saving training results"""
        results = args[0]
        uuid = results['uuid']
        self.train_results[uuid].append(results)

    def on_predict_results(self, *args):
        """Callback function for saving prediction results"""
        results = args[0]
        uuid = results['uuid']
        self.predict_results[uuid].append(results)

    def print_results(self, *args):
        """Prints out results"""
        print(args)

    #
    # Other methods
    #

    def get_info(self, list_of_devices=None) -> []:
        """
        Return list of string representations of device info for specified
        devices (by calling get_info of each device).
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
    # Example usage:
    # python neurostack.py --server_address localhost:8001 --address localhost:8002

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Run Neurostack')

    parser.add_argument('--address', type=str, default='localhost:8002',
                        help='ip:port to run Neurostack client on')
    parser.add_argument('--server_address', type=str,
                        help='ip:port of Neurostack server to connect to')
    parser.add_argument('--use_fake_data', action='store_true',
                        help='Use flag to generate fake data')

    args = parser.parse_args()

    # TODO: add something to specify which devices get passed in
    muse = Muse()
    muse.connect(fake_data=args.use_fake_data)
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
