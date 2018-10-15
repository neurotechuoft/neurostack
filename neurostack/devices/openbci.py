from devices.device import Device
import usb


class OpenBCI(Device):

    def __init__(self, device_id=None):
        pass

    def available_devices(self):
        """ Returns list of available OpenBCI devices by device name 
        
        Works on Linux, untested for other OS
        """
        devs = usb.core.find(find_all=True, idVendor=0x0403, idProduct=0x6015)
        openBCI_devices = []

        for device in devs:
            if device.manufacturer == "FTDI":   # must be run with sudo to see manufacturer
                openBCI_devices.append(device.product) # append USB name

        return openBCI_devices

