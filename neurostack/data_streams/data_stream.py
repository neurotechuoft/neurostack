"""
LSL-like object to stream data to multiple channels. Some code and helper
methods taken from https://github.com/kaczmarj/rteeg
"""
import numpy as np
import pylsl


def look_for_eeg_stream():
    """returns an inlet of the first eeg stream outlet found."""
    print("looking for an EEG stream...")
    streams = pylsl.resolve_byprop('type', 'EEG', timeout=30)
    if len(streams) == 0:
        raise (RuntimeError, "Can't find EEG stream")
    print("Start acquiring data")
    eeg_inlet = pylsl.StreamInlet(streams[0], max_chunklen=1)

    return eeg_inlet


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

    def add_channel(self, name, inlet=None):
        """
        Adds a channel to the data stream

        :param name: name of channel to add
        :param inlet: data inlet for the channel. If none is specified, then
                      data in the channel will have to be added with add_data.
        :return: None
        """
        if self.channels.get(name) is not None:
            print("Channel with name {0} already exists".format(name))
        else:
            self.channels[name] = []

    def remove_channel(self, name):
        """
        Removes a channel from the data stream

        :param name: name of channel to remove
        :return: None
        """
        if self.channels.get(name) is None:
            print("Channel with name {0} does not exist".format(name))
        else:
            self.channels.pop(name)

    def close(self):
        """Close all connections"""
        self.channels = {}

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

    def get_all_data(self, channels):
        """
        Gets (a copy of) all available data from the list of channels

        :param channels:
        :return
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
        pass

    #
    # Stream information
    #

    def list_channels(self):
        """Returns a list of all the channels"""
        return list(self.channels.keys())
