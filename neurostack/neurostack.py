from devices.muse import Muse
from socketIO_client import SocketIO
from utils import generate_uuid
from sanic import Sanic

import argparse
import asyncio
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
        self.stream_raw_data = {}

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

    def send_train_data(self, server_endpoint, uuid, eeg_data, label):
        """
        Sends training data to neurostack server

        :param server_endpoint: server API's endpoint
        :param uuid: client's UUID
        :param eeg_data: one sample of EEG data to be used for training
        :param label: this data's label
        :returns: None
        """
        args = {
            'uuid': uuid,
            'data': eeg_data,
            'label': label
        }
        self.sio_neurostack.emit(server_endpoint, args, self.on_train_results)
        self.sio_neurostack.wait_for_callbacks(seconds=1)

    def send_predict_data(self, server_endpoint, uuid, eeg_data):
        """
        Sneds prediction data to neurostack server

        :param server_endpoint: server API's endpoint
        :param uuid: client's UUID
        :param eeg_data: one sample of EEG data that we want to predict for
        :returns: None
        """
        args = {
            'uuid': uuid,
            'data': eeg_data
        }
        self.sio_neurostack.emit(server_endpoint, args, self.on_predict_results)
        self.sio_neurostack.wait_for_callbacks(seconds=1)

    def send_train_data_test(self, uuid, eeg_data, label):
        """
        Tests endpoint for sending training data to neurostack server

        :param uuid: client's UUID
        :param eeg_data: one sample of EEG data to be used for training
        :param label: this data's label
        :returns: None
        """
        args = {
            'uuid': uuid,
            'data': eeg_data,
            'label': label
        }
        self.sio_neurostack.emit("test_train", args, self.print_results)
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
        self.sio_neurostack.emit("test_predict", args, self.print_results)
        self.sio_neurostack.wait_for_callbacks(seconds=1)

    #
    # Methods for handling client-side communication
    #

    def initialize_handlers(self):
        """Initialize handlers for client-side communication"""

        # streaming raw data
        self.sio_app.on("start_streaming_raw_data", self.start_streaming_raw_data_handler)
        self.sio_app.on("stop_streaming_raw_data", self.stop_streaming_raw_data_handler)

        # training Neurostack model
        self.sio_app.on("p300_train", self.p300_train_handler)
        self.sio_app.on("p300_predict", self.p300_predict_handler)

        self.sio_app.on("left_right_train", self.left_right_train_handler)
        self.sio_app.on("left_right_predict", self.left_right_predict_handler)

        # misc
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
        
    async def start_streaming_raw_data_handler(self, sid, args):
        """
        Handler for streaming raw data

        :param sid: session ID (not important)
        :param args: arguments passed to this function. This should include:
            uuid: universally unique ID of user who wants to stop streaming
        """
        args = json.loads(args)
        uuid = args['uuid']
        self.stream_raw_data[uuid] = True

        # keep track of data from previous while loop iteration, so that the
        # same data is not sent twice.
        prev_data = None
        while self.stream_raw_data[uuid]:

            # TODO: devices[0] is the Muse that we set at the bottom, but we
            # want to support multiple or different devices
            data_stream = self.devices[0].data_stream
            eeg_channel_names = data_stream.get_eeg_channels()
            raw_data = data_stream.get_latest_data(eeg_channel_names)

            # TODO: raw data can be either a list or a dict right now, should we
            # just stick with dict?

            # in case while loop is running faster than device streaming rate
            if raw_data != prev_data:
                prev_data = raw_data
                await self.sio_app.emit('raw_data', raw_data)

    async def stop_streaming_raw_data_handler(self, sid, args):
        """
        Handler to tell neurostack to stop streaming raw data

        :param sid: session ID (not important)
        :param args: arguments passed to this function. This should include:
            uuid: universally unique ID of user who wants to stop streaming
        """
        args = json.loads(args)
        uuid = args['uuid']
        self.stream_raw_data[uuid] = False

        await self.sio_app.emit('raw_data', "streaming has stopped")

    async def p300_train_handler(self, sid, args):
        """P300 training handler"""
        args = json.loads(args)

        await self.train_handler(
            server_endpoint="p300_train",
            uuid=args['uuid'],
            timestamp=args['timestamp'],
            label=args['p300']
        )

    async def p300_predict_handler(self, sid, args):
        """P300 prediction handler"""
        args = json.loads(args)

        await self.predict_handler(
            server_endpoint="p300_predict",
            uuid=args['uuid'],
            timestamp=args['timestamp']
        )

    async def left_right_train_handler(self, sid, args):
        """Left-right training handler"""
        args = json.loads(args)

        await self.train_handler(
            server_endpoint="left_right_train",
            uuid=args['uuid'],
            timestamp=args['timestamp'],
            label=args['left']
        )

    async def left_right_predict_handler(self, sid, args):
        """Left-right prediction handler"""
        args = json.loads(args)

        await self.predict_handler(
            server_endpoint="left_right_predict",
            uuid=args['uuid'],
            timestamp=args['timestamp']
        )

    async def train_handler(self, server_endpoint, uuid, timestamp, label,
                            window=0.75):
        """
        Handler for passing training data to Neurostack

        TODO: something for sample rate

        :param server_endpoint: Neurostack server API endpoint
        :param uuid: client UUID
        :param timestamp: timestamp of data we are interested in, in unix time
        :param label: label for data
        :param window: window of data we are interested in, in seconds
        :return: None
        """
        # create list for uuid if not done already
        self.train_results[uuid] = self.train_results.get(uuid, [])

        # TODO: change API to specify device
        device = self.devices[0]

        # Wait until the device has enough data (ie. the time slice is complete)
        # then take 100ms - 750ms window for training
        while time.time() < timestamp + window:
            time.sleep(.01)

        # TODO: num_samples = window * sample rate
        timestamp -= self.devices[0].get_time_diff()
        data_dict = device.data_stream.get_eeg_data(start_time=timestamp + .1,
                                                    num_samples=128)
        data = list(data_dict.values())

        self.send_train_data(
            server_endpoint=server_endpoint,
            uuid=uuid,
            eeg_data=data,
            label=label
        )

        # wait for results
        while len(self.train_results[uuid]) == 0:
            time.sleep(.01)
        result = self.train_results[uuid].pop(0)
        await self.sio_app.emit("train", result)

    async def predict_handler(self, server_endpoint, uuid, timestamp,
                              window=0.75):
        """
        Handler for passing prediction data to Neurostack

        TODO: something for sample rate

        :param server_endpoint: Neurostack server API endpoint
        :param uuid: client UUID
        :param timestamp: timestamp of data we are interested in, in unix time
        :param window: window of data we are interested in, in seconds
        :return: None
        """
        # create list for uuid if not done already
        self.predict_results[uuid] = self.predict_results.get(uuid, [])

        # TODO: change API to specify device
        device = self.devices[0]

        # Wait until the device has enough data (ie. the time slice is complete)
        # then take 100ms - 750ms window for training. The window should
        # contain 0.65s * 256Hz = 166 samples.
        while time.time() < timestamp + window:
            time.sleep(.01)

        timestamp -= self.devices[0].get_time_diff()
        data_dict = device.data_stream.get_eeg_data(start_time=timestamp + .1,
                                                    num_samples=128)
        data = list(data_dict.values())

        self.send_predict_data(
            server_endpoint=server_endpoint,
            uuid=uuid,
            eeg_data=data
        )

        # wait for results
        while len(self.predict_results[uuid]) == 0:
            time.sleep(.01)
        result = self.predict_results[uuid].pop(0)
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
