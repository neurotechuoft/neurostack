class Neurostack():

    def __init__(self, device, subscribers=None, tags=None):
        self.device = device
        self.subscribers = subscribers
        self.tags = tags

    def start(self):
        """
        Start streaming EEG from device, and publish data to subscribers.

        :return: None
        """
        pass

    def stop(self):
        """
        Stop streaming EEG data from device, and stop publishing data to
        subscribers. Connection to device remains intact, and device is not
        turned off.

        :return: None
        """
        pass

    def shutdown(self):
        """
        Close connection to device, WebSocket connections to publishers, and tag sources.

        :return: None
        """
        pass
