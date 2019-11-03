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
        self.thread = None
        self.eeg_channel_names = None

    #
    # Connection methods
    #

    def lsl_connect(self):
        """Connects to LSL stream"""
        # get stream
        eeg_stream = look_for_eeg_stream()
        info = eeg_stream.info()

        # get channel names
        ch_names = []
        this_child = info.desc().child('channels').child('channel')
        for _ in range(info.channel_count()):
            ch_names.append(this_child.child_value('label'))
            this_child = this_child.next_sibling('channel')
        self.eeg_channel_names = ch_names

        # record data to channels
        self._thread = threading.Thread(target=self._record_lsl_data_indefinitely,
                                        name='lsl')
        self._thread.daemon = True
        self._thread.start()

    def _record_lsl_data_indefinitely(self):
        """
        Record LSL data indefinitely

        :param channel_names: channel names to stream samples to
        :return: does not return
        """
        # create channels
        for channel_name in self.eeg_channel_names:
            self.add_channel(channel_name)

        # continuously pull data
        while True:
            samples, timestamp = inlet.pull_sample()
            time_correction = inlet.time_correction()

            # add pulled samples to channels
            for i in range(len(samples)):
                self.add_data(self.eeg_channel_names[i],
                              [timestamp + time_correction] + samples[i])

    def add_channel(self, name):
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
        self.channels[channel].append(data)

    def remove_data(self, channel, data):
        """
        TODO: decide on / find out about the specific requirements of the data
        Remove a specific piece of data from a channel

        :param channel:
        :param data:
        :return:
        """
        try:
            self.channels[channel].remove(data)
        except ValueError:
            raise (ValueError, "data does not exist in channel")

    #
    # Stream information
    #

    def list_channels(self):
        """Returns a list of all the channels"""
        return list(self.channels.keys())
