class Neurostack():

    def __init__(self, devices, subscribers=None, tags=None):
        """
        Initialize a connection with an EEG device, and sets up an
        asynchronous connection with subscribers passed in.

        :param device: [Devices]
        :param subscribers:
        :param tags:
        """
        self.devices = devices
        self.subscribers = subscribers
        self.tags = tags

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

    def get_subscribers(self) -> []:
        """
        Return list of websocket subscribers that currently receive data from this neurostack.

        :return:
        """
        pass

    def print_subscribers(self) -> str:
        """
        Return string representation of websocket subscribers that currently receive data from this neurostack.

        :return:  
        """
        pass
    
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
        
