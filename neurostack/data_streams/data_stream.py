class DataStream:

    def __init__(self):
        """Initializes data stream"""
        self.channels = {}

    #
    # Connection methods
    #

    def lsl_connect(self):
        """Connects to LSL stream"""
        pass

    def add_channel(self, name):
        """
        Adds a channel to the data stream

        :param name:
        :return:
        """
        pass

    def remove_channel(self, name):
        """
        Removes a channel from the data stream

        :param name:
        :return:
        """
        pass

    def close(self):
        """Close all connections"""
        pass

    #
    # Methods for processing data
    #

    def get_data(self, channels, start_time, duration):
        """
        Takes a (copy of a) slice of data from channels at start_time for
        duration

        :param channels:
        :param start_time:
        :param duration:
        :return:
        """
        pass

    def get_latest_data(self, channels):
        """
        Gets (a copy of the) latest data entry from channels

        :param channels:
        :return:
        """
        pass

    def add_data(self, channel, data):
        """
        TODO: decide on / find out about the specific requirements of the data
        Add data to channel

        :param channel:
        :param data:
        :return:
        """
        pass

    def remove_data(self, channel, data):
        """
        TODO: decide on / find out about the specific requirements of the data
        Remove a specific piece of data from a channel

        :param channel:
        :param data:
        :return:
        """

    #
    # Stream information
    #

    def list_channels(self):
        """Returns a list of all the channels and their names / data types"""
        pass

    def list_channel_info(self, channel):
        """
        TODO: not sure if this is needed
        More in depth information on a specific channel

        :param channel:
        :return:
        """
        pass
