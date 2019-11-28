from pyOpenBCI import OpenBCICyton
from devices.device import Device
from pylsl import StreamInfo, StreamOutlet
import numpy as np

class OpenBCI(Device):

    def __init__(self, device_id=None):
        super().__init__(device_id)

    @staticmethod
    def available_devices():
        """
        Returns list of available OpenBCI devices by device name

        Works on Linux, untested for other OS
        """
        # devs = usb.core.find(find_all=True, idVendor=0x0403, idProduct=0x6015)
        # openBCI_devices = []

        # for device in devs:
        #     if device.manufacturer == "FTDI":   # must be run with sudo to see manufacturer
        #         openBCI_devices.append(device.product) # append USB name

        # return openBCI_devices

        pass  # OpenBCICyton does it internally

    def connect(self, device_id=None):
        """
        Connect to EEG device with id specified. If id is not specified,
        connect to randomly selected EEG device.

        :param device_id:
        :return:
        """
        self.openbci_cyton = OpenBCICyton( daisy=False)

    def start(self,callback) -> None:
        """
        Start streaming EEG from device, and publish data to subscribers.

        :return:
        """

        self.openbci_cyton.start_stream(callback)

    def stop(self) -> None:
        """
        Stop streaming EEG data from device, and stop publishing data to
        subscribers. Connection to device remains intact, and device is not
        turned off.

        :return:
        """
        self.openbci_cyton.stop()

    def shutdown(self) -> None:
        """
        Close connection to device, WebSocket connections to publishers, and tag
        sources.

        :return:
        """
        self.openbci_cyton.disconnect()

    def get_info(self) -> None:
        """
        Get information about the device including device type, connection type, electrode names, device type, stream time, etc...

        :return:
        """
        pass
