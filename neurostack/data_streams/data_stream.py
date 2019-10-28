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

    #
    # Methods for processing data
    #

    def get_data(self, channels, start_time, duration):
        """
        Takes a slice of data from channels at start_time for duration

        :param channels:
        :param start_time:
        :param duration:
        :return:
        """
        pass

    #
    # Stream information
    #

    def get_channels(self):
        """Returns a list of all the channels and their names / data types"""
        pass
