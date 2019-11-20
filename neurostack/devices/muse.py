from data_streams.data_stream import DataStream
from devices import Device

import pylsl
import random
import threading
import time


class Muse(Device):

    def __init__(self, device_id=None):
        super().__init__(device_id)
        self.data_stream = DataStream()

        # TODO: somehow use this line
        # self.time_diff = time.time() - self.streams['eeg'].data[-1][-1]
        self.time_diff = 0      # difference between unix and muse time

        # for generating fake data
        self._fake_muse = None
        self._fake_muse_active = False

    #
    # Private device methods for handling data streams
    #

    def _create_fake_eeg_stream(self):
        """
        Method for generating dummy EEG data for the muse. Sends randomly-
        generated data through an LSL outlet.

        :return: None
        """
        def generate_muse_data():
            """Generate 4 random floats, representing channels AF7, AF8, TP9,
            and TP10 on the muse headset"""
            return [random.random() for _ in range(4)]

        # create fake muse
        info = pylsl.StreamInfo(name='Muse', type='EEG', channel_count=4,
                                nominal_srate=256, channel_format='float32', source_id='fake muse')
        info.desc().append_child_value('manufacturer', 'Muse')
        channels = info.desc().append_child('channels')

        # set channel names and units
        for c in ['TP9-l_ear', 'FP1-l_forehead', 'FP2-r_forehead',
                  'TP10-r_ear']:
            channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "EEG")

        outlet = pylsl.StreamOutlet(info)

        # continuously push data to outlet when active
        while self._fake_muse_active:
            outlet.push_sample(generate_muse_data())
            time.sleep(0.00390625)  # 256Hz

    #
    # Public device methods
    #

    def connect(self, device_id=None, fake_data=False):
        """
        Creates data streams if there are none and connects to EEG stream
        (since that is the one that is immediately needed for use). If fake_data
        is True, then start a separate thread that generates fake data instead
        of connecting to a muse.
        """
        # create thread that runs something which continuously streams data
        if fake_data:
            eeg_data_thread = threading.Thread(target=self._create_fake_eeg_stream,
                                               name='fake muse')
            eeg_data_thread.daemon = True
            eeg_data_thread.start()

            self._fake_muse_active = True
            self._fake_muse = eeg_data_thread

        self.data_stream.lsl_connect()

    def start(self):
        """Start streaming EEG data"""
        self.data_stream.lsl_start()
        while len(self.data_stream.list_channels()) == 0:
            time.sleep(0.01)
        channel_name = [self.data_stream.list_channels()[0]]
        while
        self.time_diff = self.data_stream.get_latest_data(channel_name)

        time.sleep(2)
        print(self.data_stream.get_all_data(channel_name))


    def stop(self):
        """Stop streaming EEG data"""
        # TODO: stop streaming EEG data in data stream
        self.data_stream.lsl_stop()

    def shutdown(self):
        """Disconnect EEG stream (and stop streaming data)"""
        pass

    def get_info(self):
        pass
